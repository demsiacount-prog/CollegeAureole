import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Pencil, Trash2, Users, LayoutGrid, List as ListIcon, Eye } from 'lucide-react'
import { useAuth } from '@/auth/useAuth'
import { Badge } from '@/components/ui/Badge'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { Drawer } from '@/components/ui/Drawer'
import { EmptyState } from '@/components/ui/EmptyState'
import { PageHeader } from '@/components/ui/PageHeader'
import { TableSkeleton } from '@/components/ui/TableSkeleton'
import { fetchClasses, fetchClasseDetail, deleteClasse } from './api'
import { ClasseFormDrawer } from './ClasseFormDrawer'
import { toast } from '@/components/ui/toast'
import { extractErrorMessage } from '@/lib/api'
import { scheduleDeleteWithUndo } from '@/lib/undoDelete'
import type { Classe } from '@/features/shared/types'
import { formatDate } from '@/lib/format'

export default function ClasseListPage() {
  const { user } = useAuth()
  const canWrite = user?.role === 'admin' || user?.role === 'directeur'
  const qc = useQueryClient()

  const { data: classes = [], isLoading, isError } = useQuery({ queryKey: ['classes'], queryFn: fetchClasses })

  const [vue, setVue] = useState<'grille' | 'liste'>('grille')
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [editing, setEditing] = useState<Classe | null>(null)
  const [deleting, setDeleting] = useState<Classe | null>(null)
  const [detailId, setDetailId] = useState<number | null>(null)

  const { data: detail, isLoading: loadingDetail } = useQuery({
    queryKey: ['classe-detail', detailId],
    queryFn: () => fetchClasseDetail(detailId!),
    enabled: detailId != null,
  })

  const deleteMut = useMutation({
    mutationFn: deleteClasse,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['classes'] })
      toast('Classe supprimée.')
      setDeleting(null)
    },
    onError: (e) => toast(extractErrorMessage(e), 'error'),
  })

  function openCreate() { setEditing(null); setDrawerOpen(true) }
  function openEdit(c: Classe) { setEditing(c); setDrawerOpen(true) }

  const grouped = classes.reduce<Record<string, Classe[]>>((acc, c) => {
    const key = c.niveau
    ;(acc[key] ??= []).push(c)
    return acc
  }, {})

  return (
    <div className="w-full">
      <div className="flex flex-col gap-5">
        <PageHeader
          title="Classes"
          count={classes.length}
          countLabel={`classe${classes.length > 1 ? 's' : ''}`}
          actionLabel={canWrite ? 'Nouvelle classe' : undefined}
          onAction={canWrite ? openCreate : undefined}
        />

        <div className="flex items-center gap-3">
          <div className="ml-auto flex gap-1 rounded-[var(--radius-sm)] border border-[var(--color-border)] p-0.5">
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
            <EmptyState message="Impossible de charger la liste des classes." />
          </div>
        ) : classes.length === 0 ? (
          <div className="py-16">
            <EmptyState message="Aucune classe enregistrée pour le moment." />
          </div>
        ) : vue === 'grille' ? (
          <div className="space-y-6">
            {Object.entries(grouped).map(([niveau, cls]) => (
              <div key={niveau}>
                <div className="mb-3 flex items-center gap-2">
                  <h3 className="font-[var(--font-mono)] text-xs font-semibold uppercase tracking-wider text-[var(--color-ink-dim)]">
                    {niveau}
                  </h3>
                  <div className="h-px flex-1 bg-[var(--color-border-soft)]" />
                  <span className="text-xs text-[var(--color-ink-faint)]">{cls.length} classe{cls.length > 1 ? 's' : ''}</span>
                </div>
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  {cls.map((c) => (
                    <div
                      key={c.id}
                      className="group overflow-hidden rounded-[var(--radius-lg)] border border-[var(--color-border)] bg-[var(--color-surface)] p-5"
                    >
                      <div className="mb-4 flex items-start justify-between">
                        <div>
                          <h4 className="font-semibold text-[var(--color-ink)]">{c.nom}</h4>
                          <Badge tone="info" className="mt-1.5">{c.niveau}</Badge>
                        </div>
                        {canWrite && (
                          <div className="flex gap-1">
                            <button
                              onClick={() => openEdit(c)}
                              className="rounded-[var(--radius-sm)] p-1.5 text-[var(--color-ink-faint)] transition-colors hover:bg-[var(--color-surface-3)] hover:text-[var(--color-ink)]"
                              aria-label="Modifier"
                            >
                              <Pencil strokeWidth={1.75} className="size-4" />
                            </button>
                            <button
                              onClick={() => setDeleting(c)}
                              className="rounded-[var(--radius-sm)] p-1.5 text-[var(--color-ink-faint)] transition-colors hover:bg-[var(--color-danger-wash)] hover:text-[var(--color-danger)]"
                              aria-label="Supprimer"
                            >
                              <Trash2 strokeWidth={1.75} className="size-4" />
                            </button>
                          </div>
                        )}
                      </div>
                      <div className="flex items-center gap-4 border-t border-[var(--color-border-soft)] pt-3 text-sm text-[var(--color-ink-dim)]">
                        <button
                          onClick={() => setDetailId(c.id)}
                          className="flex items-center gap-1.5 transition-colors hover:text-[var(--color-ink)]"
                        >
                          <Users strokeWidth={1.75} className="size-3.5 text-[var(--color-ink-faint)]" />
                          Voir les élèves
                        </button>
                      </div>
                      <div className="mt-2 space-y-0.5 text-xs text-[var(--color-ink-faint)]">
                        <p>Inscription : {c.frais_inscription.toLocaleString('fr-FR')} FCFA</p>
                        <p>Mensualité : {c.mensualite.toLocaleString('fr-FR')} FCFA</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="overflow-x-auto rounded-[var(--radius-lg)] border border-[var(--color-border)]">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[var(--color-border-soft)] bg-[var(--color-surface-2)]">
                  <th className="px-5 py-3 text-left font-medium text-[var(--color-ink-dim)]">Niveau</th>
                  <th className="px-5 py-3 text-left font-medium text-[var(--color-ink-dim)]">Nom</th>
                  <th className="px-5 py-3 text-left font-medium text-[var(--color-ink-dim)]">Inscription</th>
                  <th className="px-5 py-3 text-left font-medium text-[var(--color-ink-dim)]">Mensualité</th>
                  <th className="px-5 py-3 text-right font-medium text-[var(--color-ink-dim)]">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--color-border-soft)]">
                {classes.map((c) => (
                  <tr key={c.id} className="hover:bg-[var(--color-surface-2)]">
                    <td className="px-5 py-3 text-[var(--color-ink)]">{c.niveau}</td>
                    <td className="px-5 py-3 font-medium text-[var(--color-ink)]">{c.nom}</td>
                    <td className="px-5 py-3 text-[var(--color-ink-dim)]">{c.frais_inscription.toLocaleString('fr-FR')} FCFA</td>
                    <td className="px-5 py-3 text-[var(--color-ink-dim)]">{c.mensualite.toLocaleString('fr-FR')} FCFA</td>
                    <td className="px-5 py-3 text-right">
                      <div className="flex justify-end gap-1">
                        <button
                          onClick={() => setDetailId(c.id)}
                          className="rounded-[var(--radius-sm)] p-1.5 text-[var(--color-ink-faint)] transition-colors hover:bg-[var(--color-surface-3)] hover:text-[var(--color-ink)]"
                          aria-label="Voir les élèves"
                          title="Voir les élèves"
                        >
                          <Eye size={14} strokeWidth={1.75} />
                        </button>
                        {canWrite && (
                          <button
                            onClick={() => openEdit(c)}
                            className="rounded-[var(--radius-sm)] p-1.5 text-[var(--color-ink-faint)] transition-colors hover:bg-[var(--color-surface-3)] hover:text-[var(--color-ink)]"
                            aria-label="Modifier"
                          >
                            <Pencil size={14} strokeWidth={1.75} />
                          </button>
                        )}
                        {canWrite && (
                          <button
                            onClick={() => setDeleting(c)}
                            className="rounded-[var(--radius-sm)] p-1.5 text-[var(--color-ink-faint)] transition-colors hover:bg-[var(--color-danger-wash)] hover:text-[var(--color-danger)]"
                            aria-label="Supprimer"
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

        <ClasseFormDrawer open={drawerOpen} onClose={() => setDrawerOpen(false)} classe={editing} />

        <Drawer
          open={detailId != null}
          onClose={() => setDetailId(null)}
          title={detail ? `${detail.niveau} — ${detail.nom}` : 'Détails de la classe'}
          description={detail ? `${detail.effectif_actuel} élève${detail.effectif_actuel > 1 ? 's' : ''} inscrit${detail.effectif_actuel > 1 ? 's' : ''} dans cette classe` : ''}
        >
          {loadingDetail ? (
            <TableSkeleton rows={6} />
          ) : !detail ? (
            <EmptyState message="Impossible de charger les élèves de cette classe." />
          ) : detail.eleves.length === 0 ? (
            <EmptyState message="Aucun élève affecté à cette classe." />
          ) : (
            <div className="space-y-2">
              {detail.eleves.map((e) => (
                <div
                  key={e.matricule}
                  className="flex items-center justify-between rounded-[var(--radius-sm)] border border-[var(--color-border-soft)] px-4 py-3"
                >
                  <div className="flex items-center gap-3">
                    <div className="flex size-9 shrink-0 items-center justify-center rounded-full bg-[var(--color-surface-3)] text-sm font-semibold text-[var(--color-ink)]">
                      {e.nom.charAt(0)}
                    </div>
                    <div>
                      <p className="font-medium text-[var(--color-ink)]">{e.nom} {e.prenom}</p>
                      <p className="text-xs text-[var(--color-ink-faint)]">Né{e.sexe === 'M' ? '' : 'e'} le {formatDate(e.date_de_naissance)}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-mono text-xs text-[var(--color-ink-dim)]">{e.matricule}</p>
                    {e.statut === 'actif' ? (
                      <Badge tone="success">Actif</Badge>
                    ) : (
                      <Badge tone="neutral">Inactif</Badge>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </Drawer>

        <ConfirmDialog
          open={!!deleting}
          onClose={() => setDeleting(null)}
          onConfirm={() => {
            if (deleting) {
              scheduleDeleteWithUndo(() => deleteMut.mutate(deleting.id), `Classe « ${deleting.nom} » supprimée.`)
            }
          }}
          title="Supprimer cette classe ?"
          description={deleting ? `"${deleting.niveau} — ${deleting.nom}" sera définitivement supprimée. Cette action est irréversible.` : ''}
          confirmLabel="Supprimer"
          variant="danger"
        />
      </div>
    </div>
  )
}
