import { useEffect, useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Pencil, Trash2 } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useAuth } from '@/auth/useAuth'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { EmptyState } from '@/components/ui/EmptyState'
import { Input } from '@/components/ui/Input'
import { PageHeader } from '@/components/ui/PageHeader'
import { Pagination } from '@/components/ui/Pagination'
import { SearchInput } from '@/components/ui/SearchInput'
import { TableSkeleton } from '@/components/ui/TableSkeleton'
import { Table, TableBody, TableCell, TableContainer, TableHead, TableHeader, TableRow } from '@/components/ui/Table'
import { toast } from '@/components/ui/toast'
import { extractErrorMessage } from '@/lib/api'
import { scheduleDeleteWithUndo } from '@/lib/undoDelete'
import { formatDate, formatMontant } from '@/lib/format'
import { fetchPaiements, fetchPaiementsTotal, deletePaiement } from './api'
import PaiementFormDrawer from './PaiementFormDrawer'
import type { Paiement } from './types'

const MODE_COLORS: Record<string, string> = {
  ESPECES: 'success',
  VIREMENT: 'info',
  CHEQUE: 'neutral',
  MOBILE_MONEY: 'warning',
}

const PAGE_SIZE = 50

export default function PaiementListPage() {
  const { user } = useAuth()
  const canWrite = user?.role === 'admin' || user?.role === 'directeur' || user?.role === 'comptable'
  const canDelete = user?.role === 'admin' || user?.role === 'comptable'
  const qc = useQueryClient()

  const [search, setSearch] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [dateDebut, setDateDebut] = useState('')
  const [dateFin, setDateFin] = useState('')
  const [page, setPage] = useState(1)

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(search.trim()), 300)
    return () => clearTimeout(timer)
  }, [search])

  useEffect(() => {
    setPage(1)
  }, [debouncedSearch, dateDebut, dateFin])

  const { data: paiements = [], isLoading: loadingPaiements, isFetching, isError } = useQuery({
    queryKey: ['paiements', 'liste', page, debouncedSearch, dateDebut, dateFin],
    queryFn: () => fetchPaiements({
      skip: (page - 1) * PAGE_SIZE,
      limit: PAGE_SIZE,
      q: debouncedSearch,
      date_debut: dateDebut || undefined,
      date_fin: dateFin || undefined,
    }),
  })

  const { data: total = 0 } = useQuery({
    queryKey: ['paiements', 'total', debouncedSearch, dateDebut, dateFin],
    queryFn: () => fetchPaiementsTotal({
      q: debouncedSearch,
      date_debut: dateDebut || undefined,
      date_fin: dateFin || undefined,
    }),
  })

  const totalPages = useMemo(() => Math.max(1, Math.ceil(total / PAGE_SIZE)), [total])

  useEffect(() => {
    if (page > totalPages) setPage(totalPages)
  }, [page, totalPages])

  const [drawerOpen, setDrawerOpen] = useState(false)
  const [editing, setEditing] = useState<Paiement | null>(null)
  const [deleting, setDeleting] = useState<{ id: number; label: string } | null>(null)

  const deleteMut = useMutation({
    mutationFn: deletePaiement,
    onSuccess: () => { toast('Paiement supprimé.'); qc.invalidateQueries({ queryKey: ['paiements'] }); setDeleting(null) },
    onError: (err) => toast(extractErrorMessage(err), 'error'),
  })

  return (
    <div className="w-full">
      <div className="flex flex-col gap-5">
        <PageHeader
          title="Paiements"
          count={total}
          countLabel={`paiement${total > 1 ? 's' : ''} enregistré${total > 1 ? 's' : ''}`}
          actionLabel={canWrite ? 'Nouveau paiement' : undefined}
          onAction={canWrite ? () => { setEditing(null); setDrawerOpen(true) } : undefined}
        />

        <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
          <SearchInput
            className="flex-1"
            placeholder="Rechercher par élève, code, mode…"
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
        </div>

        {loadingPaiements ? (
          <TableSkeleton rows={8} />
        ) : isError ? (
          <div className="py-16">
            <EmptyState message="Impossible de charger les paiements." />
          </div>
        ) : paiements.length === 0 ? (
          <div className="py-16">
            <EmptyState message={debouncedSearch || dateDebut || dateFin ? 'Aucun paiement ne correspond à ce filtre.' : 'Aucun paiement enregistré pour le moment.'} />
          </div>
        ) : (
          <TableContainer>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Code</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead>Inscription</TableHead>
                  <TableHead className="text-right">Montant</TableHead>
                  <TableHead>Mode</TableHead>
                  <TableHead className="hidden lg:table-cell">Observation</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {paiements.map((p) => {
                  const nomEleve = `${p.eleve_nom ?? ''} ${p.eleve_prenom ?? ''}`.trim()
                  return (
                    <TableRow key={p.id}>
                      <TableCell className="font-[var(--font-mono)] text-xs text-[var(--color-ink-dim)]">
                        {p.code_paiement ?? '—'}
                      </TableCell>
                      <TableCell className="font-[var(--font-mono)] text-xs text-[var(--color-ink-dim)]">
                        {formatDate(p.date)}
                      </TableCell>
                      <TableCell>
                        <Link to={`/app/eleves/${p.matricule_eleve ?? ''}`} className="group inline-block">
                          <p className="text-sm font-medium text-[var(--color-ink)] group-hover:text-[var(--color-brand-bright)]">
                            {nomEleve || '—'}
                          </p>
                          <p className="text-xs text-[var(--color-ink-faint)]">
                            {p.matricule_eleve ?? '—'}
                          </p>
                        </Link>
                      </TableCell>
                      <TableCell className="text-right font-medium text-[var(--color-ink)]">
                        {formatMontant(p.montant)}
                      </TableCell>
                      <TableCell>
                        {p.mode && (
                          <Badge tone={MODE_COLORS[p.mode] as 'success' | 'warning' | 'info' | 'neutral' | 'danger' ?? 'neutral'}>
                            {p.mode}
                          </Badge>
                        )}
                      </TableCell>
                      <TableCell className="hidden lg:table-cell max-w-[200px] truncate text-xs text-[var(--color-ink-faint)]">
                        {p.observation ?? '—'}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center justify-end gap-1">
                          {canWrite && (
                            <Button
                              variant="icon"
                              size="icon"
                              onClick={() => { setEditing(p); setDrawerOpen(true) }}
                              aria-label="Modifier ce paiement"
                            >
                              <Pencil strokeWidth={1.75} className="size-4" />
                            </Button>
                          )}
                          {canDelete && (
                            <Button
                              variant="icon"
                              tone="danger"
                              size="icon"
                              onClick={() => setDeleting({ id: p.id, label: `${formatDate(p.date)} — ${formatMontant(p.montant)}` })}
                              aria-label="Supprimer ce paiement"
                            >
                              <Trash2 strokeWidth={1.75} className="size-4" />
                            </Button>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          </TableContainer>
        )}

        {total > 0 && (
          <Pagination page={page} totalPages={totalPages} onChange={setPage} isFetching={isFetching} />
        )}
      </div>

      <PaiementFormDrawer
        open={drawerOpen}
        onClose={() => { setDrawerOpen(false); setEditing(null) }}
        paiement={editing}
      />

      <ConfirmDialog
        open={!!deleting}
        onClose={() => setDeleting(null)}
        onConfirm={() => {
          if (deleting) {
            setDeleting(null)
            scheduleDeleteWithUndo(() => deleteMut.mutate(deleting.id), 'Paiement supprimé.')
          }
        }}
        title="Supprimer ce paiement ?"
        description={`Êtes-vous sûr de vouloir supprimer le paiement ${deleting?.label} ? Cette action est irréversible.`}
        confirmLabel="Supprimer"
        variant="danger"
      />
    </div>
  )
}
