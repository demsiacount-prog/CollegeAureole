import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Plus, Pencil, Trash2, Users } from 'lucide-react'
import { Badge } from '@/components/ui/Badge'
import { Drawer } from '@/components/ui/Drawer'
import { Button } from '@/components/ui/Button'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { EmptyState } from '@/components/ui/EmptyState'
import { SearchInput } from '@/components/ui/SearchInput'
import { TableSkeleton } from '@/components/ui/TableSkeleton'
import { Table, TableBody, TableCell, TableContainer, TableHead, TableHeader, TableRow } from '@/components/ui/Table'
import { toast } from '@/components/ui/toast'
import { extractErrorMessage } from '@/lib/api'
import { scheduleDeleteWithUndo } from '@/lib/undoDelete'
import { useAuth } from '@/auth/useAuth'
import { fetchCours, createCours, updateCours, deleteCours } from './api'
import CoursFormDrawer from './CoursFormDrawer'
import type { Cours, CoursCreateInput } from './types'

export default function CoursListPage() {
  const { user } = useAuth()
  const canWrite = user?.role === 'admin' || user?.role === 'directeur'
  const canDelete = user?.role === 'admin'
  const qc = useQueryClient()
  const { data: cours = [], isLoading, isError } = useQuery({ queryKey: ['cours'], queryFn: fetchCours })

  const [search, setSearch] = useState('')
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [editing, setEditing] = useState<Cours | null>(null)
  const [deleting, setDeleting] = useState<Cours | null>(null)
  const [classesCours, setClassesCours] = useState<Cours | null>(null)

  const createMut = useMutation({
    mutationFn: (data: CoursCreateInput) => createCours(data),
    onSuccess: () => { toast('Cours créé avec succès'); qc.invalidateQueries({ queryKey: ['cours'] }); setDrawerOpen(false) },
    onError: (e) => toast(extractErrorMessage(e), 'error'),
  })

  const updateMut = useMutation({
    mutationFn: ({ id, data }: { id: number; data: CoursCreateInput }) => updateCours(id, data),
    onSuccess: () => { toast('Cours mis à jour'); qc.invalidateQueries({ queryKey: ['cours'] }); setDrawerOpen(false); setEditing(null) },
    onError: (e) => toast(extractErrorMessage(e), 'error'),
  })

  const deleteMut = useMutation({
    mutationFn: deleteCours,
    onSuccess: () => { toast('Cours supprimé'); qc.invalidateQueries({ queryKey: ['cours'] }); setDeleting(null) },
    onError: (e) => toast(extractErrorMessage(e), 'error'),
  })

  const filtered = cours.filter((c) => {
    const q = search.toLowerCase()
    return c.nom.toLowerCase().includes(q) || c.description.toLowerCase().includes(q) || (c.code_cours ?? '').toLowerCase().includes(q)
  })

  const handleSubmit = (data: CoursCreateInput) => {
    if (editing) updateMut.mutate({ id: editing.id, data })
    else createMut.mutate(data)
  }

  return (
    <div className="w-full">
      <div className="flex flex-col gap-5">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-2xl font-semibold tracking-tight text-[var(--color-ink)]">
              Cours
            </h2>
            <p className="mt-1 text-sm text-[var(--color-ink-dim)]">
              {cours.length} cours au programme
            </p>
          </div>
          {canWrite && (
            <Button variant="primary" onClick={() => setDrawerOpen(true)}>
              <Plus size={16} strokeWidth={1.75} className="mr-1.5" />
              Nouveau cours
            </Button>
          )}
        </div>

        <SearchInput
          className="w-full"
          placeholder="Rechercher un cours…"
          value={search}
          onChange={setSearch}
        />

        {isLoading ? (
          <TableSkeleton rows={8} />
        ) : isError ? (
          <div className="py-16">
            <EmptyState message="Impossible de charger la liste des cours." />
          </div>
        ) : filtered.length === 0 ? (
          <div className="py-16">
            <EmptyState message={search ? 'Aucun cours ne correspond à cette recherche.' : 'Aucun cours enregistré pour le moment.'} />
          </div>
        ) : (
          <TableContainer>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Nom</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead>Volume</TableHead>
                  <TableHead>Professeur</TableHead>
                  <TableHead>Classes</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.map((c) => (
                  <TableRow key={c.id}>
                    <TableCell className="font-medium text-[var(--color-ink)]">{c.nom}</TableCell>
                    <TableCell className="text-[var(--color-ink-dim)]">{c.description}</TableCell>
                    <TableCell><Badge tone="neutral">{c.volume_horaire}h</Badge></TableCell>
                    <TableCell className="text-[var(--color-ink-dim)]">
                      {c.enseignant ? `${c.enseignant.prenom} ${c.enseignant.nom}` : '—'}
                    </TableCell>
                    <TableCell>
                      <button
                        onClick={() => setClassesCours(c)}
                        className="inline-flex items-center gap-1.5 whitespace-nowrap rounded-[var(--radius-sm)] px-2 py-1 text-sm text-[var(--color-brand-bright)] transition-colors hover:bg-[var(--color-brand-wash)]"
                      >
                        <Users size={14} strokeWidth={1.75} />
                        {c.classes.length} classe{c.classes.length > 1 ? 's' : ''}
                      </button>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-1">
                        {canWrite && (
                          <button
                            onClick={() => { setEditing(c); setDrawerOpen(true) }}
                            className="rounded-[var(--radius-sm)] p-1.5 text-[var(--color-ink-faint)] transition-colors hover:bg-[var(--color-surface-3)] hover:text-[var(--color-ink)]"
                            aria-label={`Modifier ${c.nom}`}
                          >
                            <Pencil size={14} strokeWidth={1.75} />
                          </button>
                        )}
                        {canDelete && (
                          <button
                            onClick={() => setDeleting(c)}
                            className="rounded-[var(--radius-sm)] p-1.5 text-[var(--color-ink-faint)] transition-colors hover:bg-[var(--color-danger-wash)] hover:text-[var(--color-danger)]"
                            aria-label={`Supprimer ${c.nom}`}
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

      <CoursFormDrawer
        cours={editing}
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
            scheduleDeleteWithUndo(() => deleteMut.mutate(deleting.id), `Cours « ${deleting.nom} » supprimé.`)
          }
        }}
        title="Supprimer ce cours ?"
        description={`Êtes-vous sûr de vouloir supprimer "${deleting?.nom}" ? Cette action est irréversible.`}
        confirmLabel="Supprimer"
        variant="danger"
      />

      <Drawer
        open={!!classesCours}
        onClose={() => setClassesCours(null)}
        title={`Classes — ${classesCours?.nom ?? ''}`}
      >
        {classesCours && classesCours.classes.length === 0 ? (
          <p className="text-sm text-[var(--color-ink-faint)]">Aucune classe associée.</p>
        ) : (
          <div className="flex flex-col gap-2">
            {classesCours?.classes.map((cl) => (
              <div key={cl.id} className="flex items-center justify-between rounded-[var(--radius-sm)] border border-[var(--color-border-soft)] px-4 py-3">
                <div>
                  <p className="font-medium text-[var(--color-ink)]">{cl.niveau} — {cl.nom}</p>
                  {cl.salle && <p className="mt-0.5 text-xs text-[var(--color-ink-faint)]">Salle : {cl.salle.nom}</p>}
                </div>
                <Badge tone="info">{cl.niveau}</Badge>
              </div>
            ))}
          </div>
        )}
      </Drawer>
    </div>
  )
}
