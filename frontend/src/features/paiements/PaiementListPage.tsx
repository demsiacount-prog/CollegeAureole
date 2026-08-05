import { useEffect, useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Trash2 } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useAuth } from '@/auth/useAuth'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
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
import { formatDate, formatMontant } from '@/lib/format'
import { fetchPaiements, fetchPaiementsTotal, deletePaiement } from './api'
import PaiementFormDrawer from './PaiementFormDrawer'

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
  const canDelete = user?.role === 'admin'
  const qc = useQueryClient()

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

  const { data: paiements = [], isLoading: loadingPaiements, isFetching } = useQuery({
    queryKey: ['paiements', 'liste', page, debouncedSearch],
    queryFn: () => fetchPaiements({ skip: (page - 1) * PAGE_SIZE, limit: PAGE_SIZE, q: debouncedSearch }),
  })

  const { data: total = 0 } = useQuery({
    queryKey: ['paiements', 'total', debouncedSearch],
    queryFn: () => fetchPaiementsTotal({ q: debouncedSearch }),
  })

  const totalPages = useMemo(() => Math.max(1, Math.ceil(total / PAGE_SIZE)), [total])

  useEffect(() => {
    if (page > totalPages) setPage(totalPages)
  }, [page, totalPages])

  const [drawerOpen, setDrawerOpen] = useState(false)
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
          onAction={canWrite ? () => setDrawerOpen(true) : undefined}
        />

        <SearchInput
          placeholder="Rechercher par élève, reçu, mode…"
          value={search}
          onChange={setSearch}
        />

        {loadingPaiements ? (
          <TableSkeleton rows={8} />
        ) : paiements.length === 0 ? (
          <div className="py-16">
            <EmptyState message={debouncedSearch ? 'Aucun paiement ne correspond à cette recherche.' : 'Aucun paiement enregistré pour le moment.'} />
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
                      <th className="px-5 py-3 text-left font-medium text-[var(--color-ink-dim)]">Inscription</th>
                      <th className="px-5 py-3 text-right font-medium text-[var(--color-ink-dim)]">Montant</th>
                      <th className="px-5 py-3 text-left font-medium text-[var(--color-ink-dim)]">Mode</th>
                      <th className="px-5 py-3 text-left font-medium text-[var(--color-ink-dim)]">N° reçu</th>
                      <th className="px-5 py-3 text-left font-medium text-[var(--color-ink-dim)] hidden lg:table-cell">Observation</th>
                      <th className="px-5 py-3 text-right font-medium text-[var(--color-ink-dim)]">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {paiements.map((p) => {
                      const nomEleve = `${p.eleve_nom ?? ''} ${p.eleve_prenom ?? ''}`.trim()
                      return (
                        <tr key={p.id} className="border-b border-[var(--color-border-soft)] last:border-0 hover:bg-[var(--color-surface-2)]">
                          <td className="px-5 py-3 font-[var(--font-mono)] text-xs text-[var(--color-ink-dim)]">
                            {p.code_paiement ?? '—'}
                          </td>
                          <td className="px-5 py-3 font-[var(--font-mono)] text-xs text-[var(--color-ink-dim)]">
                            {formatDate(p.date)}
                          </td>
                          <td className="px-5 py-3">
                            <Link to={`/app/eleves/${p.matricule_eleve ?? ''}`} className="group inline-block">
                              <p className="text-sm font-medium text-[var(--color-ink)] group-hover:text-[var(--color-brand-bright)]">
                                {nomEleve || '—'}
                              </p>
                              <p className="text-xs text-[var(--color-ink-faint)]">
                                {p.matricule_eleve ?? '—'}
                              </p>
                            </Link>
                          </td>
                          <td className="px-5 py-3 text-right font-medium text-[var(--color-ink)]">
                            {formatMontant(p.montant)}
                          </td>
                          <td className="px-5 py-3">
                            {p.mode && (
                              <Badge tone={MODE_COLORS[p.mode] as 'success' | 'warning' | 'info' | 'neutral' | 'danger' ?? 'neutral'}>
                                {p.mode}
                              </Badge>
                            )}
                          </td>
                          <td className="px-5 py-3 font-[var(--font-mono)] text-xs text-[var(--color-ink-dim)]">
                            {p.numero_recu ?? '—'}
                          </td>
                          <td className="px-5 py-3 text-xs text-[var(--color-ink-faint)] hidden lg:table-cell max-w-[200px] truncate">
                            {p.observation ?? '—'}
                          </td>
                          <td className="px-5 py-3">
                            <div className="flex items-center justify-end gap-1">
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
                          </td>
                        </tr>
                      )
                    })}
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

      <PaiementFormDrawer open={drawerOpen} onClose={() => setDrawerOpen(false)} />

      <ConfirmDialog
        open={!!deleting}
        onClose={() => setDeleting(null)}
        onConfirm={() => {
          if (deleting) {
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
