import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Plus, Pencil, Trash2, LayoutGrid, List as ListIcon, DoorOpen } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Card, CardBody } from '@/components/ui/Card'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { EmptyState } from '@/components/ui/EmptyState'
import { SearchInput } from '@/components/ui/SearchInput'
import { TableSkeleton } from '@/components/ui/TableSkeleton'
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

  const [vue, setVue] = useState<'grille' | 'liste'>('liste')
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
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-2xl font-semibold tracking-tight text-[var(--color-ink)]">
              Salles
            </h2>
            <p className="mt-1 text-sm text-[var(--color-ink-dim)]">
              {salles.length} salles enregistrées
            </p>
          </div>
          {canWrite && (
            <Button variant="primary" onClick={() => setDrawerOpen(true)}>
              <Plus size={16} strokeWidth={1.75} className="mr-1.5" />
              Nouvelle salle
            </Button>
          )}
        </div>

        <div className="flex items-center gap-3">
          <SearchInput
            className="flex-1"
            placeholder="Rechercher une salle…"
            value={search}
            onChange={setSearch}
          />
          <div className="flex gap-1 rounded-[var(--radius-sm)] border border-[var(--color-border)] p-0.5">
            <button
              onClick={() => setVue('grille')}
              className={`flex items-center gap-1.5 rounded-[4px] px-2.5 py-1.5 text-xs font-medium transition-colors ${vue === 'grille' ? 'bg-[var(--color-surface-3)] text-[var(--color-ink)]' : 'text-[var(--color-ink-faint)]'}`}
            >
              <LayoutGrid size={13} strokeWidth={1.75} /> Grille
            </button>
            <button
              onClick={() => setVue('liste')}
              className={`flex items-center gap-1.5 rounded-[4px] px-2.5 py-1.5 text-xs font-medium transition-colors ${vue === 'liste' ? 'bg-[var(--color-surface-3)] text-[var(--color-ink)]' : 'text-[var(--color-ink-faint)]'}`}
            >
              <ListIcon size={13} strokeWidth={1.75} /> Liste
            </button>
          </div>
        </div>

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
        ) : vue === 'grille' ? (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {filtered.map((s) => (
              <div
                key={s.id}
                className="group overflow-hidden rounded-[var(--radius-lg)] border border-[var(--color-border)] bg-[var(--color-surface)] p-5"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-[var(--color-brand-wash)] text-sm font-semibold text-[var(--color-brand)]">
                      <DoorOpen strokeWidth={1.75} className="size-5" />
                    </div>
                    <div>
                      <p className="font-semibold text-[var(--color-ink)]">{s.nom}</p>
                      <p className="mt-0.5 text-xs text-[var(--color-ink-faint)]">
                        {s.capacite != null ? `${s.capacite} places` : 'Capacité non définie'}
                      </p>
                    </div>
                  </div>
                  <div className="flex gap-1">
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
                </div>
              </div>
            ))}
          </div>
        ) : (
          <Card>
            <CardBody>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-[var(--color-border)]">
                      <th className="pb-3 text-left font-medium text-[var(--color-ink-dim)]">Nom</th>
                      <th className="pb-3 text-left font-medium text-[var(--color-ink-dim)]">Capacité</th>
                      <th className="pb-3 text-right font-medium text-[var(--color-ink-dim)]">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[var(--color-border-soft)]">
                    {filtered.map((s) => (
                      <tr key={s.id} className="hover:bg-[var(--color-surface-2)]">
                        <td className="py-3 text-[var(--color-ink)] font-medium">{s.nom}</td>
                        <td className="py-3 text-[var(--color-ink-dim)]">
                          {s.capacite != null ? `${s.capacite} places` : '—'}
                        </td>
                        <td className="py-3 text-right">
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
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardBody>
          </Card>
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
