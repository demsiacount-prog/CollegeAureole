import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Pencil, Trash2 } from 'lucide-react'
import { useAuth } from '@/auth/useAuth'
import { Avatar } from '@/components/ui/Avatar'
import { Badge } from '@/components/ui/Badge'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { EmptyState } from '@/components/ui/EmptyState'
import { PageHeader } from '@/components/ui/PageHeader'
import { Pagination } from '@/components/ui/Pagination'
import { SearchInput } from '@/components/ui/SearchInput'
import { TableSkeleton } from '@/components/ui/TableSkeleton'
import { Table, TableBody, TableCell, TableContainer, TableHead, TableHeader, TableRow } from '@/components/ui/Table'
import { toast } from '@/components/ui/toast'
import { extractErrorMessage } from '@/lib/api'
import { scheduleDeleteWithUndo } from '@/lib/undoDelete'
import { fetchEnseignants, fetchEnseignantsTotal, deleteEnseignant } from './api'
import EnseignantFormDrawer from './EnseignantFormDrawer'
import type { Enseignant } from './types'

const PAGE_SIZE = 50

export default function EnseignantListPage() {
  const { user } = useAuth()
  const canWrite = user?.role === 'admin' || user?.role === 'directeur'
  const canDelete = user?.role === 'admin'
  const qc = useQueryClient()

  const [search, setSearch] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [page, setPage] = useState(1)
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [editing, setEditing] = useState<Enseignant | null>(null)
  const [deleting, setDeleting] = useState<Enseignant | null>(null)

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(search.trim()), 300)
    return () => clearTimeout(timer)
  }, [search])

  useEffect(() => {
    setPage(1)
  }, [debouncedSearch])

  const { data: enseignants = [], isLoading, isFetching, isError } = useQuery({
    queryKey: ['enseignants', 'liste', page, debouncedSearch],
    queryFn: () => fetchEnseignants({ skip: (page - 1) * PAGE_SIZE, limit: PAGE_SIZE, q: debouncedSearch }),
  })

  const { data: total = 0 } = useQuery({
    queryKey: ['enseignants', 'total', debouncedSearch],
    queryFn: () => fetchEnseignantsTotal(debouncedSearch),
  })

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE))

  useEffect(() => {
    if (page > totalPages) setPage(totalPages)
  }, [page, totalPages])

  const deleteMut = useMutation({
    mutationFn: deleteEnseignant,
    onSuccess: () => { toast('Enseignant supprimé.'); qc.invalidateQueries({ queryKey: ['enseignants'] }); setDeleting(null) },
    onError: (err) => toast(extractErrorMessage(err), 'error'),
  })

  function openCreate() { setEditing(null); setDrawerOpen(true) }
  function openEdit(e: Enseignant) { setEditing(e); setDrawerOpen(true) }

  return (
    <div className="w-full">
      <div className="flex flex-col gap-5">
        <PageHeader
          title="Enseignants"
          count={total}
          countLabel={`enseignant${total > 1 ? 's' : ''} enregistré${total > 1 ? 's' : ''}`}
          actionLabel={canWrite ? 'Nouvel enseignant' : undefined}
          onAction={canWrite ? openCreate : undefined}
        />

        <SearchInput
          placeholder="Rechercher par nom, matricule, spécialité…"
          value={search}
          onChange={setSearch}
        />

        {isLoading ? (
          <TableSkeleton rows={8} />
        ) : isError ? (
          <div className="py-16">
            <EmptyState message="Impossible de charger la liste des enseignants." />
          </div>
        ) : enseignants.length === 0 ? (
          <div className="py-16">
            <EmptyState message={debouncedSearch ? 'Aucun enseignant ne correspond à cette recherche.' : 'Aucun enseignant enregistré pour le moment.'} />
          </div>
        ) : (
          <TableContainer>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Enseignant</TableHead>
                  <TableHead>Spécialité</TableHead>
                  <TableHead>Téléphone</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {enseignants.map((e) => (
                  <TableRow key={e.matricule}>
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <Avatar nom={e.nom} prenom={e.prenom} size="sm" />
                        <div>
                          <Link to={`/app/enseignants/${e.matricule}`} className="font-medium text-[var(--color-ink)] hover:text-[var(--color-brand-bright)]">
                            {e.prenom} {e.nom}
                          </Link>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge tone="neutral">{e.specialite}</Badge>
                    </TableCell>
                    <TableCell className="font-[var(--font-mono)] text-xs text-[var(--color-ink-dim)]">{e.telephone}</TableCell>
                    <TableCell>
                      <div className="flex items-center justify-end gap-1">
                        {canWrite && (
                          <button
                            onClick={() => openEdit(e)}
                            className="rounded-[var(--radius-sm)] p-1.5 text-[var(--color-ink-faint)] transition-colors hover:bg-[var(--color-surface-3)] hover:text-[var(--color-ink)]"
                            aria-label={`Modifier ${e.prenom} ${e.nom}`}
                          >
                            <Pencil strokeWidth={1.75} className="size-4" />
                          </button>
                        )}
                        {canDelete && (
                          <button
                            onClick={() => setDeleting(e)}
                            className="rounded-[var(--radius-sm)] p-1.5 text-[var(--color-ink-faint)] transition-colors hover:bg-[var(--color-danger-wash)] hover:text-[var(--color-danger)]"
                            aria-label={`Supprimer ${e.prenom} ${e.nom}`}
                          >
                            <Trash2 strokeWidth={1.75} className="size-4" />
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

        {total > 0 && (
          <Pagination page={page} totalPages={totalPages} onChange={setPage} isFetching={isFetching} />
        )}
      </div>

      <EnseignantFormDrawer
        open={drawerOpen}
        onClose={() => { setDrawerOpen(false); setEditing(null) }}
        enseignant={editing}
      />

      <ConfirmDialog
        open={!!deleting}
        onClose={() => setDeleting(null)}
        onConfirm={() => {
          if (deleting) {
            setDeleting(null)
            scheduleDeleteWithUndo(() => deleteMut.mutate(deleting.matricule), 'Enseignant supprimé.')
          }
        }}
        title="Supprimer cet enseignant ?"
        description={`Êtes-vous sûr de vouloir supprimer "${deleting?.prenom} ${deleting?.nom}" ? Cette action est irréversible.`}
        confirmLabel="Supprimer"
        variant="danger"
      />
    </div>
  )
}
