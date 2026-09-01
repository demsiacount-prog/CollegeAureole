import { useEffect, useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Pencil, Trash2 } from 'lucide-react'
import { useAuth } from '@/auth/useAuth'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { EmptyState } from '@/components/ui/EmptyState'
import { Input } from '@/components/ui/Input'
import { PageHeader } from '@/components/ui/PageHeader'
import { Pagination } from '@/components/ui/Pagination'
import { SearchInput } from '@/components/ui/SearchInput'
import { Select } from '@/components/ui/Select'
import { TableSkeleton } from '@/components/ui/TableSkeleton'
import { Table, TableBody, TableCell, TableContainer, TableHead, TableHeader, TableRow } from '@/components/ui/Table'
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
  const [dateDebut, setDateDebut] = useState('')
  const [dateFin, setDateFin] = useState('')
  const [page, setPage] = useState(1)

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(search.trim()), 300)
    return () => clearTimeout(timer)
  }, [search])

  useEffect(() => {
    setPage(1)
  }, [debouncedSearch, catFilter, dateDebut, dateFin])

  const { data: depenses = [], isLoading, isFetching, isError } = useQuery({
    queryKey: ['depenses', 'liste', page, debouncedSearch, catFilter, dateDebut, dateFin],
    queryFn: () => fetchDepenses({
      skip: (page - 1) * PAGE_SIZE,
      limit: PAGE_SIZE,
      q: debouncedSearch,
      categorie: catFilter || undefined,
      date_debut: dateDebut || undefined,
      date_fin: dateFin || undefined,
    }),
  })

  const { data: compte = { total: 0, total_montant: 0 } } = useQuery({
    queryKey: ['depenses', 'total', debouncedSearch, catFilter, dateDebut, dateFin],
    queryFn: () => fetchDepensesCompte({
      q: debouncedSearch,
      categorie: catFilter || undefined,
      date_debut: dateDebut || undefined,
      date_fin: dateFin || undefined,
    }),
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

        <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
          <SearchInput
            className="flex-1"
            placeholder="Rechercher par libellé, description…"
            value={search}
            onChange={setSearch}
          />
          <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
            <Input
              type="date"
              label="Du"
              className="w-full sm:w-44"
              value={dateDebut}
              onChange={(e) => setDateDebut(e.target.value)}
            />
            <Input
              type="date"
              label="Au"
              className="w-full sm:w-44"
              value={dateFin}
              onChange={(e) => setDateFin(e.target.value)}
            />
          </div>
          <Select value={catFilter} onChange={(e) => setCatFilter(e.target.value)} className="w-full sm:w-48">
            <option value="">Toutes catégories</option>
            {CATEGORIES.map((c) => <option key={c} value={c}>{CATEGORIE_LABELS[c]}</option>)}
          </Select>
        </div>

        {isLoading ? (
          <TableSkeleton rows={8} />
        ) : isError ? (
          <div className="py-16">
            <EmptyState message="Impossible de charger les dépenses." />
          </div>
        ) : depenses.length === 0 ? (
          <div className="py-16">
            <EmptyState message={debouncedSearch || catFilter || dateDebut || dateFin ? 'Aucune dépense ne correspond à ce filtre.' : 'Aucune dépense enregistrée pour le moment.'} />
          </div>
        ) : (
          <TableContainer>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Code</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead>Libellé</TableHead>
                  <TableHead>Catégorie</TableHead>
                  <TableHead className="text-right">Montant</TableHead>
                  <TableHead className="hidden lg:table-cell">Description</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {depenses.map((d) => (
                  <TableRow key={d.id}>
                    <TableCell className="font-[var(--font-mono)] text-xs text-[var(--color-ink-dim)]">
                      {d.code_depense ?? '—'}
                    </TableCell>
                    <TableCell className="font-[var(--font-mono)] text-xs text-[var(--color-ink-dim)]">
                      {formatDate(d.date)}
                    </TableCell>
                    <TableCell className="font-medium text-[var(--color-ink)]">{d.libelle}</TableCell>
                    <TableCell>
                      <Badge tone={(CATEGORIE_COLORS[d.categorie] as 'success' | 'warning' | 'info' | 'neutral' | 'danger') ?? 'neutral'}>
                        {CATEGORIE_LABELS[d.categorie]}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right font-[var(--font-mono)] text-[15px] font-semibold text-[var(--color-ink)]">
                      {formatMontant(d.montant)}
                    </TableCell>
                    <TableCell className="hidden lg:table-cell max-w-[200px] truncate text-xs text-[var(--color-ink-faint)]">
                      {d.description ?? '—'}
                    </TableCell>
                    <TableCell>
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
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
              {total > 0 && (
                <tfoot>
                  <TableRow>
                    <TableCell colSpan={4} className="text-right font-semibold text-[var(--color-warning)]">
                      Total filtré
                    </TableCell>
                    <TableCell className="text-right font-[var(--font-mono)] text-[15px] font-semibold text-[var(--color-warning)]">
                      {formatMontant(compte.total_montant)}
                    </TableCell>
                    <TableCell colSpan={2} />
                  </TableRow>
                </tfoot>
              )}
            </Table>
          </TableContainer>
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
            setDeleting(null)
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
