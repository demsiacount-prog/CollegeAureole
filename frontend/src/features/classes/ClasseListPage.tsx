import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Pencil, Trash2, Eye } from 'lucide-react'
import { useAuth } from '@/auth/useAuth'
import { Badge } from '@/components/ui/Badge'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { Drawer } from '@/components/ui/Drawer'
import { EmptyState } from '@/components/ui/EmptyState'
import { PageHeader } from '@/components/ui/PageHeader'
import { TableSkeleton } from '@/components/ui/TableSkeleton'
import { Table, TableBody, TableCell, TableContainer, TableHead, TableHeader, TableRow } from '@/components/ui/Table'
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
        ) : (
          <TableContainer>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Niveau</TableHead>
                  <TableHead>Nom</TableHead>
                  <TableHead>Salle</TableHead>
                  <TableHead>Inscription</TableHead>
                  <TableHead>Mensualité</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {classes.map((c) => (
                  <TableRow key={c.id}>
                    <TableCell className="text-[var(--color-ink)]">{c.niveau}</TableCell>
                    <TableCell className="font-medium text-[var(--color-ink)]">{c.nom}</TableCell>
                    <TableCell className="text-[var(--color-ink-dim)]">{c.salle?.nom ?? '—'}</TableCell>
                    <TableCell className="text-[var(--color-ink-dim)]">{c.frais_inscription.toLocaleString('fr-FR')} FCFA</TableCell>
                    <TableCell className="text-[var(--color-ink-dim)]">{c.mensualite.toLocaleString('fr-FR')} FCFA</TableCell>
                    <TableCell className="text-right">
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
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
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
              setDeleting(null)
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
