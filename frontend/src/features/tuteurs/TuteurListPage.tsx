import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Pencil, Trash2 } from 'lucide-react'
import { useAuth } from '@/auth/useAuth'
import { Avatar } from '@/components/ui/Avatar'
import { Badge } from '@/components/ui/Badge'
import { Card, CardBody } from '@/components/ui/Card'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { EmptyState } from '@/components/ui/EmptyState'
import { PageHeader } from '@/components/ui/PageHeader'
import { Pagination } from '@/components/ui/Pagination'
import { SearchInput } from '@/components/ui/SearchInput'
import { TableSkeleton } from '@/components/ui/TableSkeleton'
import { toast } from '@/components/ui/toast'
import { extractErrorMessage } from '@/lib/api'
import { scheduleDeleteWithUndo } from '@/lib/undoDelete'
import { fetchTuteurs, fetchTuteursTotal, deleteTuteur } from './api'
import { TuteurFormDrawer } from './TuteurFormDrawer'
import type { Tuteur } from '@/features/shared/types'

const PAGE_SIZE = 50

export default function TuteurListPage() {
  const { user } = useAuth()
  const canWrite = user?.role === 'admin' || user?.role === 'directeur'
  const canDelete = user?.role === 'admin'
  const qc = useQueryClient()

  const [search, setSearch] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [page, setPage] = useState(1)
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [editing, setEditing] = useState<Tuteur | null>(null)
  const [deleting, setDeleting] = useState<Tuteur | null>(null)

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(search.trim()), 300)
    return () => clearTimeout(timer)
  }, [search])

  useEffect(() => {
    setPage(1)
  }, [debouncedSearch])

  const { data: tuteurs = [], isLoading, isFetching, isError } = useQuery({
    queryKey: ['tuteurs', 'liste', page, debouncedSearch],
    queryFn: () => fetchTuteurs({ skip: (page - 1) * PAGE_SIZE, limit: PAGE_SIZE, q: debouncedSearch }),
  })

  const { data: total = 0 } = useQuery({
    queryKey: ['tuteurs', 'total', debouncedSearch],
    queryFn: () => fetchTuteursTotal(debouncedSearch),
  })

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE))

  useEffect(() => {
    if (page > totalPages) setPage(totalPages)
  }, [page, totalPages])

  const deleteMut = useMutation({
    mutationFn: deleteTuteur,
    onSuccess: () => { toast('Tuteur supprimé.'); qc.invalidateQueries({ queryKey: ['tuteurs'] }); setDeleting(null) },
    onError: (err) => toast(extractErrorMessage(err), 'error'),
  })

  function openCreate() { setEditing(null); setDrawerOpen(true) }
  function openEdit(t: Tuteur) { setEditing(t); setDrawerOpen(true) }

  return (
    <div className="w-full">
      <div className="flex flex-col gap-5">
        <PageHeader
          title="Tuteurs"
          count={total}
          countLabel={`tuteur${total > 1 ? 's' : ''} enregistré${total > 1 ? 's' : ''}`}
          actionLabel={canWrite ? 'Nouveau tuteur' : undefined}
          onAction={canWrite ? openCreate : undefined}
        />

        <SearchInput
          placeholder="Rechercher par nom, téléphone, profession…"
          value={search}
          onChange={setSearch}
        />

        {isLoading ? (
          <TableSkeleton rows={8} />
        ) : isError ? (
          <div className="py-16">
            <EmptyState message="Impossible de charger la liste des tuteurs." />
          </div>
        ) : tuteurs.length === 0 ? (
          <div className="py-16">
            <EmptyState message={debouncedSearch ? 'Aucun tuteur ne correspond à cette recherche.' : 'Aucun tuteur enregistré pour le moment.'} />
          </div>
        ) : (
          <Card>
            <CardBody className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-[var(--color-border)]">
                      <th className="px-5 py-3 text-left font-medium text-[var(--color-ink-dim)]">Tuteur</th>
                      <th className="px-5 py-3 text-left font-medium text-[var(--color-ink-dim)]">Profession</th>
                      <th className="px-5 py-3 text-left font-medium text-[var(--color-ink-dim)]">Téléphone</th>
                      <th className="px-5 py-3 text-right font-medium text-[var(--color-ink-dim)]">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {tuteurs.map((t) => (
                      <tr key={t.id} className="border-b border-[var(--color-border-soft)] last:border-0 hover:bg-[var(--color-surface-2)]">
                        <td className="px-5 py-3">
                          <div className="flex items-center gap-3">
                            <Avatar nom={t.nom} prenom={t.prenom} size="sm" />
                            <div>
                              <Link to={`/app/tuteurs/${t.id}`} className="font-medium text-[var(--color-ink)] hover:text-[var(--color-brand-bright)]">
                                {t.prenom} {t.nom}
                              </Link>
                            </div>
                          </div>
                        </td>
                        <td className="px-5 py-3">
                          <Badge tone="neutral">{t.profession || '—'}</Badge>
                        </td>
                        <td className="px-5 py-3 font-[var(--font-mono)] text-xs text-[var(--color-ink-dim)]">{t.telephone}</td>
                        <td className="px-5 py-3">
                          <div className="flex items-center justify-end gap-1">
                            {canWrite && (
                              <button
                                onClick={() => openEdit(t)}
                                className="rounded-[var(--radius-sm)] p-1.5 text-[var(--color-ink-faint)] transition-colors hover:bg-[var(--color-surface-3)] hover:text-[var(--color-ink)]"
                                aria-label={`Modifier ${t.prenom} ${t.nom}`}
                              >
                                <Pencil strokeWidth={1.75} className="size-4" />
                              </button>
                            )}
                            {canDelete && (
                              <button
                                onClick={() => setDeleting(t)}
                                className="rounded-[var(--radius-sm)] p-1.5 text-[var(--color-ink-faint)] transition-colors hover:bg-[var(--color-danger-wash)] hover:text-[var(--color-danger)]"
                                aria-label={`Supprimer ${t.prenom} ${t.nom}`}
                              >
                                <Trash2 strokeWidth={1.75} className="size-4" />
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

        {total > 0 && (
          <Pagination page={page} totalPages={totalPages} onChange={setPage} isFetching={isFetching} />
        )}
      </div>

      <TuteurFormDrawer
        open={drawerOpen}
        onClose={() => { setDrawerOpen(false); setEditing(null) }}
        tuteur={editing ?? undefined}
      />

      <ConfirmDialog
        open={!!deleting}
        onClose={() => setDeleting(null)}
        onConfirm={() => {
          if (deleting) {
            scheduleDeleteWithUndo(
              () => deleteMut.mutate(deleting.id),
              `Tuteur « ${deleting.prenom} ${deleting.nom} » supprimé.`,
            )
          }
        }}
        title="Supprimer ce tuteur ?"
        description={`Êtes-vous sûr de vouloir supprimer "${deleting?.prenom} ${deleting?.nom}" ? Cette action est irréversible.`}
        confirmLabel="Supprimer"
        variant="danger"
      />
    </div>
  )
}
