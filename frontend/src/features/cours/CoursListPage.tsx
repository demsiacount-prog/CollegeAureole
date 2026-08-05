import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Plus, Pencil, Trash2, LayoutGrid, List as ListIcon } from 'lucide-react'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { EmptyState } from '@/components/ui/EmptyState'
import { SearchInput } from '@/components/ui/SearchInput'
import { TableSkeleton } from '@/components/ui/TableSkeleton'
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

  const [vue, setVue] = useState<'grille' | 'liste'>('grille')
  const [search, setSearch] = useState('')
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [editing, setEditing] = useState<Cours | null>(null)
  const [deleting, setDeleting] = useState<Cours | null>(null)

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

        <div className="flex items-center gap-3">
          <SearchInput
            className="flex-1"
            placeholder="Rechercher un cours…"
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
            <EmptyState message="Impossible de charger la liste des cours." />
          </div>
        ) : filtered.length === 0 ? (
          <div className="py-16">
            <EmptyState message={search ? 'Aucun cours ne correspond à cette recherche.' : 'Aucun cours enregistré pour le moment.'} />
          </div>
        ) : vue === 'grille' ? (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {filtered.map((c) => (
              <div
                key={c.id}
                className="group overflow-hidden rounded-[var(--radius-lg)] border border-[var(--color-border)] bg-[var(--color-surface)] p-5"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    
                    <div>
                      <p className="font-semibold text-[var(--color-ink)]">{c.nom}</p>
                      <p className="mt-0.5 text-xs text-[var(--color-ink-faint)]">{c.description}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    
                    {(canWrite || canDelete) && (
                      <div className="flex gap-1">
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
                    )}
                  </div>
                </div>
                <div className="mt-3 space-y-1.5 border-t border-[var(--color-border-soft)] pt-3 text-sm">
                  {c.enseignant && (
                    <p className="text-[var(--color-ink-dim)]">
                      <span className="text-[var(--color-ink-faint)]">Prof. </span>
                      {c.enseignant.prenom} {c.enseignant.nom}
                    </p>
                  )}
                  {c.classes.length > 0 && (
                    <div className="flex flex-wrap gap-1.5">
                      {c.classes.map((cl) => (
                        <Badge key={cl.id} tone="info">
                          {cl.niveau} {cl.nom}
                        </Badge>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="overflow-x-auto rounded-[var(--radius-lg)] border border-[var(--color-border)]">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[var(--color-border-soft)] bg-[var(--color-surface-2)]">
                  <th className="px-5 py-3 text-left font-medium text-[var(--color-ink-dim)]">Nom</th>
                  <th className="px-5 py-3 text-left font-medium text-[var(--color-ink-dim)]">Description</th>
                  <th className="px-5 py-3 text-left font-medium text-[var(--color-ink-dim)]">Volume</th>
                  <th className="px-5 py-3 text-left font-medium text-[var(--color-ink-dim)]">Professeur</th>
                  <th className="px-5 py-3 text-left font-medium text-[var(--color-ink-dim)]">Classes</th>
                  <th className="px-5 py-3 text-right font-medium text-[var(--color-ink-dim)]">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--color-border-soft)]">
                {filtered.map((c) => (
                  <tr key={c.id} className="hover:bg-[var(--color-surface-2)]">
                    <td className="px-5 py-3 font-medium text-[var(--color-ink)]">{c.nom}</td>
                    <td className="px-5 py-3 text-[var(--color-ink-dim)]">{c.description}</td>
                    <td className="px-5 py-3"><Badge tone="neutral">{c.volume_horaire}h</Badge></td>
                    <td className="px-5 py-3 text-[var(--color-ink-dim)]">
                      {c.enseignant ? `${c.enseignant.prenom} ${c.enseignant.nom}` : '—'}
                    </td>
                    <td className="px-5 py-3">
                      <div className="flex flex-wrap gap-1.5">
                        {c.classes.map((cl) => (
                          <Badge key={cl.id} tone="info">{cl.niveau} {cl.nom}</Badge>
                        ))}
                      </div>
                    </td>
                    <td className="px-5 py-3 text-right">
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
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
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
    </div>
  )
}
