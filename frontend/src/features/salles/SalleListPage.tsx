import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Pencil, Trash2 } from 'lucide-react'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { EmptyState } from '@/components/ui/EmptyState'
import { PageHeader } from '@/components/ui/PageHeader'
import { SearchInput } from '@/components/ui/SearchInput'
import { TableSkeleton } from '@/components/ui/TableSkeleton'
import { Table, TableBody, TableCell, TableContainer, TableHead, TableHeader, TableRow } from '@/components/ui/Table'
import { toast } from '@/components/ui/toast'
import { extractErrorMessage } from '@/lib/api'
import { scheduleDeleteWithUndo } from '@/lib/undoDelete'
import { useAuth } from '@/auth/useAuth'
import { fetchSalles, createSalle, updateSalle, deleteSalle } from './api'
import SalleFormDrawer from './SalleFormDrawer'
import type { Salle, SalleCreateInput } from './types'

export default function SalleListPage() {
  const { user } = useAuth()
  const canWrite = user?.role === 'admin' || user?.role === 'directeur'
  const canDelete = user?.role === 'admin'
  const qc = useQueryClient()
  const { data: salles = [], isLoading, isError } = useQuery({ queryKey: ['salles'], queryFn: fetchSalles })

  const [search, setSearch] = useState('')
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [editing, setEditing] = useState<Salle | null>(null)
  const [deleting, setDeleting] = useState<Salle | null>(null)

  const createMut = useMutation({
    mutationFn: (data: SalleCreateInput) => createSalle(data),
    onSuccess: () => { toast('Salle créée'); qc.invalidateQueries({ queryKey: ['salles'] }); setDrawerOpen(false) },
    onError: (e) => toast(extractErrorMessage(e), 'error'),
  })

  const updateMut = useMutation({
    mutationFn: ({ id, data }: { id: number; data: SalleCreateInput }) => updateSalle(id, data),
    onSuccess: () => { toast('Salle mise à jour'); qc.invalidateQueries({ queryKey: ['salles'] }); setDrawerOpen(false); setEditing(null) },
    onError: (e) => toast(extractErrorMessage(e), 'error'),
  })

  const deleteMut = useMutation({
    mutationFn: deleteSalle,
    onSuccess: () => { toast('Salle supprimée'); qc.invalidateQueries({ queryKey: ['salles'] }); setDeleting(null) },
    onError: (e) => toast(extractErrorMessage(e), 'error'),
  })

  const filtered = salles.filter((s) => s.nom.toLowerCase().includes(search.toLowerCase()) || (s.code_salle ?? '').toLowerCase().includes(search.toLowerCase()))

  const handleSubmit = (data: SalleCreateInput) => {
    if (editing) updateMut.mutate({ id: editing.id, data })
    else createMut.mutate(data)
  }

  return (
    <div className="w-full">
      <div className="flex flex-col gap-5">
        <PageHeader
          title="Salles"
          count={salles.length}
          countLabel="salles enregistrées"
          actionLabel={canWrite ? 'Nouvelle salle' : undefined}
          onAction={canWrite ? () => setDrawerOpen(true) : undefined}
        />

        <SearchInput
          className="w-full"
          placeholder="Rechercher une salle…"
          value={search}
          onChange={setSearch}
        />

        {isLoading ? (
          <TableSkeleton rows={8} />
        ) : isError ? (
          <div className="py-16">
            <EmptyState message="Impossible de charger la liste des salles." />
          </div>
        ) : filtered.length === 0 ? (
          <div className="py-16">
            <EmptyState message={search ? 'Aucune salle ne correspond à cette recherche.' : 'Aucune salle enregistrée pour le moment.'} />
          </div>
        ) : (
          <TableContainer>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Nom</TableHead>
                  <TableHead>Capacité</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.map((s) => (
                  <TableRow key={s.id}>
                    <TableCell className="font-medium text-[var(--color-ink)]">{s.nom}</TableCell>
                    <TableCell className="text-[var(--color-ink-dim)]">
                      {s.capacite != null ? `${s.capacite} places` : '—'}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-1">
                        {canWrite && (
                          <button
                            onClick={() => { setEditing(s); setDrawerOpen(true) }}
                            className="rounded-[var(--radius-sm)] p-1.5 text-[var(--color-ink-faint)] transition-colors hover:bg-[var(--color-surface-3)] hover:text-[var(--color-ink)]"
                            aria-label={`Modifier ${s.nom}`}
                          >
                            <Pencil size={14} strokeWidth={1.75} />
                          </button>
                        )}
                        {canDelete && (
                          <button
                            onClick={() => setDeleting(s)}
                            className="rounded-[var(--radius-sm)] p-1.5 text-[var(--color-ink-faint)] transition-colors hover:bg-[var(--color-danger-wash)] hover:text-[var(--color-danger)]"
                            aria-label={`Supprimer ${s.nom}`}
                          >
                            <Trash2 size={14} strokeWidth={1.75} />
                          </button>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </div>

      <SalleFormDrawer
        salle={editing}
        open={drawerOpen}
        onClose={() => { setDrawerOpen(false); setEditing(null) }}
        onSubmit={handleSubmit}
      />

      <ConfirmDialog
        open={!!deleting}
        onClose={() => setDeleting(null)}
        onConfirm={() => {
          if (deleting) {
            setDeleting(null)
            scheduleDeleteWithUndo(() => deleteMut.mutate(deleting.id), `Salle « ${deleting.nom} » supprimée.`)
          }
        }}
        title="Supprimer cette salle ?"
        description={`Êtes-vous sûr de vouloir supprimer "${deleting?.nom}" ? Cette action est irréversible.`}
        confirmLabel="Supprimer"
        variant="danger"
      />
    </div>
  )
}
