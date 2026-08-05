import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Plus, Search, Trash2, Power, Lock } from 'lucide-react'
import { Card, CardBody } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { TableSkeleton } from '@/components/ui/TableSkeleton'
import { EmptyState } from '@/components/ui/EmptyState'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { toast } from '@/components/ui/toast'
import { extractErrorMessage } from '@/lib/api'
import { scheduleDeleteWithUndo } from '@/lib/undoDelete'
import { fetchAnneesScolaires, createAnneeScolaire, deleteAnneeScolaire, activerAnneeScolaire, cloturerAnneeScolaire } from './api'
import AnneeScolaireFormDrawer from './AnneeScolaireFormDrawer'
import type { AnneeScolaire, AnneeScolaireCreateInput } from './types'

export default function AnneeScolaireListPage() {
  const qc = useQueryClient()
  const { data: annees = [], isLoading, isError } = useQuery({ queryKey: ['annees-scolaires'], queryFn: fetchAnneesScolaires })

  const [search, setSearch] = useState('')
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [deleting, setDeleting] = useState<AnneeScolaire | null>(null)

  const createMut = useMutation({
    mutationFn: (data: AnneeScolaireCreateInput) => createAnneeScolaire(data),
    onSuccess: () => { toast('Année scolaire créée'); qc.invalidateQueries({ queryKey: ['annees-scolaires'] }); setDrawerOpen(false) },
    onError: (e) => toast(extractErrorMessage(e), 'error'),
  })

  const deleteMut = useMutation({
    mutationFn: deleteAnneeScolaire,
    onSuccess: () => { toast('Année scolaire supprimée'); qc.invalidateQueries({ queryKey: ['annees-scolaires'] }); setDeleting(null) },
    onError: (e) => toast(extractErrorMessage(e), 'error'),
  })

  const activerMut = useMutation({
    mutationFn: activerAnneeScolaire,
    onSuccess: () => { toast('Année scolaire activée'); qc.invalidateQueries({ queryKey: ['annees-scolaires'] }) },
    onError: (e) => toast(extractErrorMessage(e), 'error'),
  })

  const cloturerMut = useMutation({
    mutationFn: cloturerAnneeScolaire,
    onSuccess: () => { toast('Année scolaire clôturée'); qc.invalidateQueries({ queryKey: ['annees-scolaires'] }) },
    onError: (e) => toast(extractErrorMessage(e), 'error'),
  })

  const filtered = annees.filter((a) => a.libelle.toLowerCase().includes(search.toLowerCase()))

  return (
    <div className="w-full">
      <div className="flex flex-col gap-5">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-2xl font-semibold tracking-tight text-[var(--color-ink)]">
              Années scolaires
            </h2>
            <p className="mt-1 text-sm text-[var(--color-ink-dim)]">
              {annees.length} années enregistrées
            </p>
          </div>
          <Button variant="primary" onClick={() => setDrawerOpen(true)}>
            <Plus size={16} strokeWidth={1.75} className="mr-1.5" />
            Nouvelle année
          </Button>
        </div>

        <div className="relative max-w-sm">
          <Search strokeWidth={1.75} className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-[var(--color-ink-faint)]" />
          <Input
            placeholder="Rechercher une année…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>

        {isLoading ? (
          <TableSkeleton rows={8} />
        ) : isError ? (
          <div className="py-16">
            <EmptyState message="Impossible de charger la liste des années scolaires." />
          </div>
        ) : filtered.length === 0 ? (
          <div className="py-16">
            <EmptyState message={search ? 'Aucune année ne correspond à cette recherche.' : 'Aucune année scolaire enregistrée.'} />
          </div>
        ) : (
          <Card>
            <CardBody>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-[var(--color-border)]">
                      <th className="pb-3 text-left font-medium text-[var(--color-ink-dim)]">Libellé</th>
                      <th className="pb-3 text-left font-medium text-[var(--color-ink-dim)]">Période</th>
                      <th className="pb-3 text-left font-medium text-[var(--color-ink-dim)]">Statut</th>
                      <th className="pb-3 text-right font-medium text-[var(--color-ink-dim)]">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[var(--color-border-soft)]">
                    {filtered.map((a) => (
                      <tr key={a.id} className="hover:bg-[var(--color-surface-2)]">
                        <td className="py-3 text-[var(--color-ink)] font-medium">{a.libelle}</td>
                        <td className="py-3 text-[var(--color-ink-dim)]">
                          {new Date(a.date_debut).toLocaleDateString('fr-FR')} — {new Date(a.date_fin).toLocaleDateString('fr-FR')}
                        </td>
                        <td className="py-3">
                          <div className="flex gap-1.5">
                            {a.cloturee ? (
                              <Badge tone="neutral">Clôturée</Badge>
                            ) : a.active ? (
                              <Badge tone="success">Active</Badge>
                            ) : (
                              <Badge tone="info">Inactive</Badge>
                            )}
                          </div>
                        </td>
                        <td className="py-3 text-right">
                          <div className="flex justify-end gap-1">
                            {!a.active && !a.cloturee && (
                              <button
                                onClick={() => activerMut.mutate(a.id)}
                                className="rounded-[var(--radius-sm)] p-1.5 text-[var(--color-ink-faint)] transition-colors hover:bg-[var(--color-success-wash)] hover:text-[var(--color-success)]"
                                aria-label={`Activer ${a.libelle}`}
                                title="Activer"
                              >
                                <Power size={14} strokeWidth={1.75} />
                              </button>
                            )}
                            {a.active && !a.cloturee && (
                              <button
                                onClick={() => cloturerMut.mutate(a.id)}
                                className="rounded-[var(--radius-sm)] p-1.5 text-[var(--color-ink-faint)] transition-colors hover:bg-[var(--color-warning-wash)] hover:text-[var(--color-warning)]"
                                aria-label={`Clôturer ${a.libelle}`}
                                title="Clôturer"
                              >
                                <Lock size={14} strokeWidth={1.75} />
                              </button>
                            )}
                            {!a.cloturee && (
                              <button
                                onClick={() => setDeleting(a)}
                                className="rounded-[var(--radius-sm)] p-1.5 text-[var(--color-ink-faint)] transition-colors hover:bg-[var(--color-danger-wash)] hover:text-[var(--color-danger)]"
                                aria-label={`Supprimer ${a.libelle}`}
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

      <AnneeScolaireFormDrawer
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        onSubmit={(data) => createMut.mutate(data)}
      />

      <ConfirmDialog
        open={!!deleting}
        onClose={() => setDeleting(null)}
        onConfirm={() => {
          if (deleting) {
            setDeleting(null)
            scheduleDeleteWithUndo(() => deleteMut.mutate(deleting.id), `Année scolaire « ${deleting.libelle} » supprimée.`)
          }
        }}
        title="Supprimer cette année scolaire ?"
        description={`Êtes-vous sûr de vouloir supprimer "${deleting?.libelle}" ? Tous les trimestres associés seront supprimés.`}
        confirmLabel="Supprimer"
        variant="danger"
      />
    </div>
  )
}
