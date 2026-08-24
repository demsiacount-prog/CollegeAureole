import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { clsx } from 'clsx'
import { Plus, Trash2, ChevronLeft } from 'lucide-react'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { EmptyState } from '@/components/ui/EmptyState'
import { Pagination } from '@/components/ui/Pagination'
import { SearchInput } from '@/components/ui/SearchInput'
import { Select } from '@/components/ui/Select'
import { TableSkeleton } from '@/components/ui/TableSkeleton'
import { Table, TableBody, TableCell, TableContainer, TableHead, TableHeader, TableRow } from '@/components/ui/Table'
import { Avatar } from '@/components/ui/Avatar'
import { toast } from '@/components/ui/toast'
import { extractErrorMessage } from '@/lib/api'
import { scheduleDeleteWithUndo } from '@/lib/undoDelete'
import { formatDate } from '@/lib/format'
import { useAuth } from '@/auth/useAuth'
import { fetchAnneesScolaires } from '@/features/annees_scolaires/api'
import { fetchInscriptions, fetchInscriptionsTotal, deleteInscription, createInscription } from './api'
import InscriptionWizard from './InscriptionWizard'
import InscriptionFormDrawer from './InscriptionFormDrawer'
import type { Inscription } from './types'

type Tab = 'liste' | 'nouvelle'

const statutTone = (s: string): 'success' | 'warning' | 'danger' | 'neutral' => {
  if (s === 'Inscrit') return 'success'
  if (s === 'Redoublant') return 'warning'
  if (s === 'Exclu') return 'danger'
  return 'neutral'
}

const PAGE_SIZE = 50

export default function InscriptionListPage() {
  const { user } = useAuth()
  const canWrite = user?.role === 'admin' || user?.role === 'directeur'
  const canDelete = user?.role === 'admin'
  const qc = useQueryClient()
  const { data: annees = [] } = useQuery({ queryKey: ['annees-scolaires'], queryFn: fetchAnneesScolaires })

  const [tab, setTab] = useState<Tab>('liste')
  const [search, setSearch] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [filterAnnee, setFilterAnnee] = useState('')
  const [filterStatut, setFilterStatut] = useState('')
  const [page, setPage] = useState(1)
  const [deleting, setDeleting] = useState<Inscription | null>(null)
  const [drawerOpen, setDrawerOpen] = useState(false)

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(search.trim()), 300)
    return () => clearTimeout(timer)
  }, [search])

  useEffect(() => {
    setPage(1)
  }, [debouncedSearch, filterAnnee, filterStatut])

  const listParams = {
    ...(filterAnnee ? { id_annee_scolaire: Number(filterAnnee) } : {}),
    ...(filterStatut ? { statut: filterStatut } : {}),
  }

  const { data: inscriptions = [], isLoading, isFetching, isError } = useQuery({
    queryKey: ['inscriptions', filterAnnee, filterStatut, debouncedSearch, page],
    queryFn: () => fetchInscriptions({
      ...listParams,
      q: debouncedSearch,
      skip: (page - 1) * PAGE_SIZE,
      limit: PAGE_SIZE,
    }),
  })

  const { data: total = 0 } = useQuery({
    queryKey: ['inscriptions', 'total', filterAnnee, filterStatut, debouncedSearch],
    queryFn: () => fetchInscriptionsTotal({ ...listParams, q: debouncedSearch }),
  })

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE))

  useEffect(() => {
    if (page > totalPages) setPage(totalPages)
  }, [page, totalPages])

  const { data: statsTotal = 0 } = useQuery({
    queryKey: ['inscriptions', 'stats', 'total', filterAnnee],
    queryFn: () => fetchInscriptionsTotal({ ...(filterAnnee ? { id_annee_scolaire: Number(filterAnnee) } : {}) }),
  })
  const { data: statsInscrits = 0 } = useQuery({
    queryKey: ['inscriptions', 'stats', 'inscrits', filterAnnee],
    queryFn: () => fetchInscriptionsTotal({ ...(filterAnnee ? { id_annee_scolaire: Number(filterAnnee) } : {}), statut: 'Inscrit' }),
  })
  const { data: statsRedoublants = 0 } = useQuery({
    queryKey: ['inscriptions', 'stats', 'redoublants', filterAnnee],
    queryFn: () => fetchInscriptionsTotal({ ...(filterAnnee ? { id_annee_scolaire: Number(filterAnnee) } : {}), statut: 'Redoublant' }),
  })
  const { data: statsExclus = 0 } = useQuery({
    queryKey: ['inscriptions', 'stats', 'exclus', filterAnnee],
    queryFn: () => fetchInscriptionsTotal({ ...(filterAnnee ? { id_annee_scolaire: Number(filterAnnee) } : {}), statut: 'Exclu' }),
  })

  const stats = {
    total: statsTotal,
    inscrits: statsInscrits,
    redoublants: statsRedoublants,
    exclus: statsExclus,
  }

  const deleteMut = useMutation({
    mutationFn: deleteInscription,
    onSuccess: () => { toast('Inscription supprimée'); qc.invalidateQueries({ queryKey: ['inscriptions'] }); setDeleting(null) },
    onError: (e) => toast(extractErrorMessage(e), 'error'),
  })

  return (
    <div className="w-full">
      <div className="flex flex-col gap-5">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-2xl font-semibold tracking-tight text-[var(--color-ink)]">
              Inscriptions
            </h2>
            <p className="mt-1 text-sm text-[var(--color-ink-dim)]">
              {total} inscription{total > 1 ? 's' : ''}
            </p>
          </div>
          {tab === 'liste' && canWrite && (
            <Button variant="primary" onClick={() => setTab('nouvelle')}>
              <Plus size={16} strokeWidth={1.75} className="mr-1.5" />
              Nouvelle inscription
            </Button>
          )}
          {tab === 'nouvelle' && (
            <Button variant="secondary" onClick={() => setTab('liste')}>
              <ChevronLeft size={14} strokeWidth={1.75} className="mr-1.5" />
              Retour à la liste
            </Button>
          )}
        </div>

        <div className="flex gap-1 w-fit rounded-[var(--radius-sm)] bg-[var(--color-surface-2)] p-1">
          {(canWrite ? (['liste', 'nouvelle'] as Tab[]) : (['liste'] as Tab[])).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={clsx(
                'rounded px-4 py-1.5 text-sm font-medium transition-all',
                tab === t
                  ? 'bg-[var(--color-surface)] text-[var(--color-ink)] shadow-[var(--shadow-soft)]'
                  : 'bg-transparent text-[var(--color-ink-dim)] hover:text-[var(--color-ink)]',
              )}
            >
              {t === 'liste' ? 'Inscriptions en cours' : 'Nouvelle inscription'}
            </button>
          ))}
        </div>

        {tab === 'liste' && (
          <>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
              {[
                { label: 'Total inscriptions' },
                { label: 'Inscrits' },
                { label: 'Redoublants' },
                { label: 'Exclus' },
              ].map((s, idx) => {
                const value = idx === 0 ? stats.total : idx === 1 ? stats.inscrits : idx === 2 ? stats.redoublants : stats.exclus
                return (
                  <Card key={s.label} className="flex flex-col justify-between p-4 min-h-[96px]">
                    <p className="text-sm font-medium text-[var(--color-ink-dim)]">{s.label}</p>
                    <p className="mt-3 text-3xl font-medium text-[var(--color-ink)]">{value}</p>
                  </Card>
                )
              })}
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <SearchInput
                className="flex-1"
                placeholder="Rechercher par nom, prénom ou matricule…"
                value={search}
                onChange={setSearch}
              />
              <Select label="" value={filterAnnee} onChange={(e) => setFilterAnnee(e.target.value)}>
                <option value="">Toutes les années</option>
                {annees.map((a) => (
                  <option key={a.id} value={a.id}>{a.libelle}</option>
                ))}
              </Select>
              <Select label="" value={filterStatut} onChange={(e) => setFilterStatut(e.target.value)}>
                <option value="">Tous les statuts</option>
                <option value="Inscrit">Inscrit</option>
                <option value="Redoublant">Redoublant</option>
                <option value="Transféré">Transféré</option>
                <option value="Exclu">Exclu</option>
              </Select>
            </div>

            {isLoading ? (
              <TableSkeleton rows={8} />
            ) : isError ? (
              <div className="py-16">
                <EmptyState message="Impossible de charger les inscriptions." />
              </div>
            ) : inscriptions.length === 0 ? (
              <div className="py-16">
                <EmptyState message={debouncedSearch ? 'Aucune inscription trouvée.' : 'Aucune inscription enregistrée.'} />
              </div>
            ) : (
              <TableContainer>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Eleve</TableHead>
                      <TableHead>Année</TableHead>
                      <TableHead>Date</TableHead>
                      <TableHead>Statut</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {inscriptions.map((i) => (
                      <TableRow key={i.id}>
                        <TableCell>
                          <div className="flex items-center gap-3">
                            <Link to={`/app/eleves/${i.matricule_eleve}`} className="flex items-center gap-3 group">
                              <Avatar nom={i.eleve_nom ?? ''} prenom={i.eleve_prenom ?? ''} size="sm" />
                              <div>
                                <p className="text-sm text-[var(--color-ink)] group-hover:text-[var(--color-brand-bright)]">{i.eleve_nom ?? '—'} {i.eleve_prenom ?? '—'}</p>
                              </div>
                            </Link>
                          </div>
                        </TableCell>
                        <TableCell className="text-[var(--color-ink-dim)]">
                          {annees.find((a) => a.id === i.id_annee_scolaire)?.libelle ?? '—'}
                        </TableCell>
                        <TableCell className="text-[var(--color-ink-dim)]">{formatDate(i.date_inscription)}</TableCell>
                        <TableCell>
                          <Badge tone={statutTone(i.statut)}>{i.statut}</Badge>
                        </TableCell>
                        <TableCell className="text-right">
                          {canDelete && (
                            <button
                              onClick={() => setDeleting(i)}
                              className="rounded-[var(--radius-sm)] p-1.5 text-[var(--color-ink-faint)] transition-colors hover:bg-[var(--color-danger-wash)] hover:text-[var(--color-danger)]"
                              aria-label="Supprimer"
                            >
                              <Trash2 size={14} strokeWidth={1.75} />
                            </button>
                          )}
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
          </>
        )}

        {tab === 'nouvelle' && (
          <div className="flex flex-col gap-4">
            <div className="flex gap-2">
              <Button variant="secondary" onClick={() => setDrawerOpen(true)}>
                <Plus size={16} strokeWidth={1.75} className="mr-1.5" />
                Inscrire un élève existant
              </Button>
            </div>
            <InscriptionWizard
              onComplete={() => {
                qc.invalidateQueries({ queryKey: ['inscriptions'] })
                setTab('liste')
              }}
              onCancel={() => setTab('liste')}
              canImport={user?.role === 'admin'}
            />
          </div>
        )}
      </div>

      <ConfirmDialog
        open={!!deleting}
        onClose={() => setDeleting(null)}
        onConfirm={() => {
          if (deleting) {
            setDeleting(null)
            scheduleDeleteWithUndo(() => deleteMut.mutate(deleting.id), 'Inscription supprimée.')
          }
        }}
        title="Supprimer cette inscription ?"
        description={`Supprimer l'inscription ${deleting?.code_inscription ?? `n°${deleting?.id}`} de ${deleting?.eleve_nom ?? ''} ${deleting?.eleve_prenom ?? ''} ?`}
        confirmLabel="Supprimer"
        variant="danger"
      />

      <InscriptionFormDrawer
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        onSubmit={async (data) => {
          await createInscription(data)
          setDrawerOpen(false)
          qc.invalidateQueries({ queryKey: ['inscriptions'] })
        }}
      />
    </div>
  )
}
