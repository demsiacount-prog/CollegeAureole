import { useEffect, useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Pencil, Trash2 } from 'lucide-react'
import { useAuth } from '@/auth/useAuth'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Card, CardBody } from '@/components/ui/Card'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { EmptyState } from '@/components/ui/EmptyState'
import { PageHeader } from '@/components/ui/PageHeader'
import { Pagination } from '@/components/ui/Pagination'
import { SearchInput } from '@/components/ui/SearchInput'
import { Select } from '@/components/ui/Select'
import { TableSkeleton } from '@/components/ui/TableSkeleton'
import { toast } from '@/components/ui/toast'
import { extractErrorMessage } from '@/lib/api'
import { scheduleDeleteWithUndo } from '@/lib/undoDelete'
import { formatDate, formatMontant } from '@/lib/format'
import { fetchDepenses, fetchDepensesCompte, deleteDepense } from './api'
import { CATEGORIES, CATEGORIE_LABELS, type Depense } from './types'
import DepenseFormDrawer from './DepenseFormDrawer'

const CATEGORIE_COLORS: Record<string, string> = {
  SALAIRES: 'info',
  FOURNITURES: 'neutral',
  ENTRETIEN: 'warning',
  ELECTRICITE: 'success',
  EAU: 'success',
  TRANSPORT: 'warning',
  ALIMENTATION: 'danger',
  MATERIEL: 'info',
}

const PAGE_SIZE = 50

export default function DepenseListPage() {
  const { user } = useAuth()
  const canWrite = user?.role === 'admin' || user?.role === 'directeur' || user?.role === 'comptable'
  const canDelete = user?.role === 'admin'
  const qc = useQueryClient()

  const [search, setSearch] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [catFilter, setCatFilter] = useState('')
  const [page, setPage] = useState(1)

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(search.trim()), 300)
    return () => clearTimeout(timer)
  }, [search])

  useEffect(() => {
    setPage(1)
  }, [debouncedSearch, catFilter])

  const { data: depenses = [], isLoading, isFetching } = useQuery({
    queryKey: ['depenses', 'liste', page, debouncedSearch, catFilter],
    queryFn: () => fetchDepenses({
      skip: (page - 1) * PAGE_SIZE,
      limit: PAGE_SIZE,
      q: debouncedSearch,
      categorie: catFilter || undefined,
    }),
  })

  const { data: compte = { total: 0, total_montant: 0 } } = useQuery({
    queryKey: ['depenses', 'total', debouncedSearch, catFilter],
    queryFn: () => fetchDepensesCompte({ q: debouncedSearch, categorie: catFilter || undefined }),
  })

  const total = compte.total
  const totalPages = useMemo(() => Math.max(1, Math.ceil(total / PAGE_SIZE)), [total])

  useEffect(() => {
    if (page > totalPages) setPage(totalPages)
  }, [page, totalPages])

  const [drawerOpen, setDrawerOpen] = useState(false)
  const [editing, setEditing] = useState<Depense | null>(null)
  const [deleting, setDeleting] = useState<Depense | null>(null)

  const deleteMut = useMutation({
    mutationFn: deleteDepense,
    onSuccess: () => { toast('Dépense supprimée.'); qc.invalidateQueries({ queryKey: ['depenses'] }); setDeleting(null) },
    onError: (err) => toast(extractErrorMessage(err), 'error'),
  })

  return (
    <div className="w-full">
      <div className="flex flex-col gap-5">
        <PageHeader
          title="Dépenses"
          count={total}
          countLabel={`dépense${total > 1 ? 's' : ''} — Total filtré : ${formatMontant(compte.total_montant)}`}
          actionLabel={canWrite ? 'Nouvelle dépense' : undefined}
          onAction={canWrite ? () => { setEditing(null); setDrawerOpen(true) } : undefined}
        />

        <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
          <SearchInput
            className="flex-1"
            placeholder="Rechercher par libellé, description…"
            value={search}
            onChange={setSearch}
          />
          <Select value={catFilter} onChange={(e) => setCatFilter(e.target.value)} className="w-full sm:w-48">
            <option value="">Toutes catégories</option>
            {CATEGORIES.map((c) => <option key={c} value={c}>{CATEGORIE_LABELS[c]}</option>)}
          </Select>
        </div>

        {isLoading ? (
          <TableSkeleton rows={8} />
        ) : depenses.length === 0 ? (
          <div className="py-16">
            <EmptyState message={debouncedSearch || catFilter ? 'Aucune dépense ne correspond à ce filtre.' : 'Aucune dépense enregistrée pour le moment.'} />
          </div>
        ) : (
          <Card>
            <CardBody className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-[var(--color-border)]">
                      <th className="px-5 py-3 text-left font-medium text-[var(--color-ink-dim)]">Code</th>
                      <th className="px-5 py-3 text-left font-medium text-[var(--color-ink-dim)]">Date</th>
                      <th className="px-5 py-3 text-left font-medium text-[var(--color-ink-dim)]">Libellé</th>
                      <th className="px-5 py-3 text-left font-medium text-[var(--color-ink-dim)]">Catégorie</th>
                      <th className="px-5 py-3 text-right font-medium text-[var(--color-ink-dim)]">Montant</th>
                      <th className="px-5 py-3 text-left font-medium text-[var(--color-ink-dim)] hidden lg:table-cell">Description</th>
                      <th className="px-5 py-3 text-right font-medium text-[var(--color-ink-dim)]">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {depenses.map((d) => (
                      <tr key={d.id} className="border-b border-[var(--color-border-soft)] last:border-0 hover:bg-[var(--color-surface-2)]">
                        <td className="px-5 py-3 font-[var(--font-mono)] text-xs text-[var(--color-ink-dim)]">
                          {d.code_depense ?? '—'}
                        </td>
                        <td className="px-5 py-3 font-[var(--font-mono)] text-xs text-[var(--color-ink-dim)]">
                          {formatDate(d.date)}
                        </td>
                        <td className="px-5 py-3 font-medium text-[var(--color-ink)]">{d.libelle}</td>
                        <td className="px-5 py-3">
                          <Badge tone={(CATEGORIE_COLORS[d.categorie] as 'success' | 'warning' | 'info' | 'neutral' | 'danger') ?? 'neutral'}>
                            {CATEGORIE_LABELS[d.categorie]}
                          </Badge>
                        </td>
                        <td className="px-5 py-3 text-right font-medium text-[var(--color-ink)]">
                          {formatMontant(d.montant)}
                        </td>
                        <td className="px-5 py-3 text-xs text-[var(--color-ink-faint)] hidden lg:table-cell max-w-[200px] truncate">
                          {d.description ?? '—'}
                        </td>
                        <td className="px-5 py-3">
                          <div className="flex items-center justify-end gap-1">
                            {canWrite && (
                              <Button
                                variant="icon"
                                size="icon"
                                onClick={() => { setEditing(d); setDrawerOpen(true) }}
                                aria-label={`Modifier ${d.libelle}`}
                              >
                                <Pencil strokeWidth={1.75} className="size-4" />
                              </Button>
                            )}
                            {canDelete && (
                              <Button
                                variant="icon"
                                tone="danger"
                                size="icon"
                                onClick={() => setDeleting(d)}
                                aria-label={`Supprimer ${d.libelle}`}
                              >
                                <Trash2 strokeWidth={1.75} className="size-4" />
                              </Button>
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

      <DepenseFormDrawer
        open={drawerOpen}
        onClose={() => { setDrawerOpen(false); setEditing(null) }}
        depense={editing}
      />

      <ConfirmDialog
        open={!!deleting}
        onClose={() => setDeleting(null)}
        onConfirm={() => {
          if (deleting) {
            scheduleDeleteWithUndo(
              () => deleteMut.mutate(deleting.id),
              `Dépense « ${deleting.libelle} » supprimée.`,
            )
          }
        }}
        title="Supprimer cette dépense ?"
        description={`Êtes-vous sûr de vouloir supprimer « ${deleting?.libelle} » (${formatMontant(deleting?.montant ?? 0)}) ? Cette action est irréversible.`}
        confirmLabel="Supprimer"
        variant="danger"
      />
    </div>
  )
}
