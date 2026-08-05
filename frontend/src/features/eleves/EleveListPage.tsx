import { useEffect, useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { UserCheck, UserX, Pencil } from 'lucide-react'
import { useAuth } from '@/auth/useAuth'
import { Avatar } from '@/components/ui/Avatar'
import { Badge } from '@/components/ui/Badge'
import { EmptyState } from '@/components/ui/EmptyState'
import { PageHeader } from '@/components/ui/PageHeader'
import { Pagination } from '@/components/ui/Pagination'
import { SearchInput } from '@/components/ui/SearchInput'
import { TableSkeleton } from '@/components/ui/TableSkeleton'
import { activerEleve, createEleve, desactiverEleve, fetchEleves, fetchElevesTotal, updateEleve } from './api'
import { EleveFormDrawer } from './EleveFormDrawer'
import type { Eleve } from './types'

const PAGE_SIZE = 50

export default function EleveListPage() {
  const { user } = useAuth()
  const canWrite = user?.role === 'admin' || user?.role === 'directeur'
  const queryClient = useQueryClient()

  const [search, setSearch] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [page, setPage] = useState(1)

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(search.trim()), 300)
    return () => clearTimeout(timer)
  }, [search])

  useEffect(() => {
    setPage(1)
  }, [debouncedSearch])

  const { data: eleves = [], isLoading, isFetching } = useQuery({
    queryKey: ['eleves', 'liste', page, debouncedSearch],
    queryFn: () => fetchEleves({ skip: (page - 1) * PAGE_SIZE, limit: PAGE_SIZE, q: debouncedSearch }),
  })

  const { data: total = 0 } = useQuery({
    queryKey: ['eleves', 'total', debouncedSearch],
    queryFn: () => fetchElevesTotal(debouncedSearch),
  })

  const totalPages = useMemo(() => Math.max(1, Math.ceil(total / PAGE_SIZE)), [total])

  useEffect(() => {
    if (page > totalPages) setPage(totalPages)
  }, [page, totalPages])

  const [drawerOpen, setDrawerOpen] = useState(false)
  const [editing, setEditing] = useState<Eleve | null>(null)

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['eleves'] })
  }

  const createMutation = useMutation({ mutationFn: createEleve, onSuccess: invalidate })
  const updateMutation = useMutation({
    mutationFn: ({ matricule, payload }: { matricule: string; payload: Parameters<typeof updateEleve>[1] }) =>
      updateEleve(matricule, payload),
    onSuccess: invalidate,
  })
  const activerMutation = useMutation({ mutationFn: activerEleve, onSuccess: invalidate })
  const desactiverMutation = useMutation({ mutationFn: desactiverEleve, onSuccess: invalidate })

  function openCreate() {
    setEditing(null)
    setDrawerOpen(true)
  }

  function openEdit(eleve: Eleve) {
    setEditing(eleve)
    setDrawerOpen(true)
  }

  return (
    <div className="w-full">
      <div className="flex flex-col gap-5">
        <PageHeader
          title="Élèves"
          count={total}
          countLabel={`élève${total > 1 ? 's' : ''} enregistré${total > 1 ? 's' : ''}`}
          actionLabel={canWrite ? 'Nouvel élève' : undefined}
          onAction={canWrite ? openCreate : undefined}
        />

      <SearchInput
        placeholder="Rechercher par nom, matricule, classe…"
        value={search}
        onChange={setSearch}
      />

      <div className="overflow-hidden rounded-[var(--radius-lg)] border border-[var(--color-border)] bg-[var(--color-surface)]">
        {isLoading ? (
          <TableSkeleton rows={8} />
        ) : eleves.length === 0 ? (
          <div className="py-16">
            <EmptyState message={debouncedSearch ? 'Aucun élève ne correspond à cette recherche.' : 'Aucun élève enregistré pour le moment.'} />
          </div>
        ) : (
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-[var(--color-border)] text-sm font-medium text-[var(--color-ink-dim)]">
                <th className="px-5 py-3 font-medium">Élève</th>
                <th className="px-5 py-3 font-medium">Matricule</th>
                <th className="px-5 py-3 font-medium">Classe</th>
                <th className="px-5 py-3 font-medium">Tuteur</th>
                <th className="px-5 py-3 font-medium">Statut</th>
                <th className="px-5 py-3 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {eleves.map((eleve) => (
                <tr key={eleve.matricule} className="group border-b border-[var(--color-border-soft)] last:border-0 hover:bg-[var(--color-surface-2)]">
                  <td className="px-5 py-3">
                    <Link to={`/app/eleves/${eleve.matricule}`} className="flex items-center gap-3 group">
                      <Avatar nom={eleve.nom} prenom={eleve.prenom} photo={eleve.photo} size="sm" />
                      <span className="font-medium text-[var(--color-ink)] group-hover:text-[var(--color-brand-bright)]">
                        {eleve.prenom} {eleve.nom}
                      </span>
                    </Link>
                  </td>
                  <td className="px-5 py-3 font-[var(--font-mono)] text-xs text-[var(--color-ink-dim)]">{eleve.matricule}</td>
                  <td className="px-5 py-3 text-[var(--color-ink-dim)]">
                    {eleve.classe ? `${eleve.classe.niveau} — ${eleve.classe.nom}` : <span className="text-[var(--color-ink-faint)]">Non affecté</span>}
                  </td>
                  <td className="px-5 py-3 text-[var(--color-ink-dim)]">
                    {eleve.tuteur.prenom} {eleve.tuteur.nom}
                  </td>
                  <td className="px-5 py-3">
                    <Badge tone={eleve.statut === 'actif' ? 'success' : 'neutral'}>
                      {eleve.statut === 'actif' ? 'Actif' : 'Inactif'}
                    </Badge>
                  </td>
                  <td className="px-5 py-3">
                    <div className="flex items-center justify-end gap-1 opacity-0 transition-all group-hover:opacity-100">
                      {canWrite && (
                        <>
                          <button
                            title="Modifier"
                            onClick={() => openEdit(eleve)}
                            className="rounded-[var(--radius-sm)] p-1.5 text-[var(--color-ink-faint)] transition-colors hover:bg-[var(--color-surface-3)] hover:text-[var(--color-ink)]"
                          >
                            <Pencil strokeWidth={1.75} className="size-4" />
                          </button>
                          {eleve.statut === 'actif' ? (
                            <button
                              title="Désactiver"
                              onClick={() => desactiverMutation.mutate(eleve.matricule)}
                              className="rounded-[var(--radius-sm)] p-1.5 text-[var(--color-ink-faint)] transition-colors hover:bg-[var(--color-danger-wash)] hover:text-[var(--color-danger)]"
                            >
                              <UserX strokeWidth={1.75} className="size-4" />
                            </button>
                          ) : (
                            <button
                              title="Activer"
                              onClick={() => activerMutation.mutate(eleve.matricule)}
                              className="rounded-[var(--radius-sm)] p-1.5 text-[var(--color-ink-faint)] transition-colors hover:bg-[var(--color-success-wash)] hover:text-[var(--color-success)]"
                            >
                              <UserCheck strokeWidth={1.75} className="size-4" />
                            </button>
                          )}
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {total > 0 && (
        <Pagination page={page} totalPages={totalPages} onChange={setPage} isFetching={isFetching} />
      )}

      <EleveFormDrawer
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        eleve={editing}
        onCreate={(payload) => createMutation.mutateAsync(payload)}
        onUpdate={(matricule, payload) => updateMutation.mutateAsync({ matricule, payload })}
      />
      </div>
    </div>
  )
}
