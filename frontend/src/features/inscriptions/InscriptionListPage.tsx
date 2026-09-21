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
import { PageHeader } from '@/components/ui/PageHeader'
import { PageToolbar, ToolbarSearch, ToolbarFilter } from '@/components/ui/PageToolbar'
import { Pagination } from '@/components/ui/Pagination'
import { TableSkeleton } from '@/components/ui/TableSkeleton'
import { Table, TableBody, TableCell, TableContainer, TableHead, TableHeader, TableRow } from '@/components/ui/Table'
import { Avatar } from '@/components/ui/Avatar'
import { toast } from '@/components/ui/toast'
import { extractErrorMessage } from '@/lib/api'
import { scheduleDeleteWithUndo } from '@/lib/undoDelete'
import { formatDate } from '@/lib/format'
import { fetchAnneesScolaires } from '@/features/annees_scolaires/api'
import { useAnneeActive } from '@/features/annees_scolaires/useAnneeActive'
import { fetchClasses } from '@/features/classes/api'
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
  const canWrite = true
  const canDelete = true
  const qc = useQueryClient()
  const { data: annees = [] } = useQuery({ queryKey: ['annees-scolaires'], queryFn: fetchAnneesScolaires })
  const { data: classes = [] } = useQuery({ queryKey: ['classes'], queryFn: fetchClasses })

  const { data: activeAnnee } = useAnneeActive()

  const [tab, setTab] = useState<Tab>('liste')
  const [search, setSearch] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const filterAnnee = activeAnnee ? String(activeAnnee.id) : ''
  const [filterClasse, setFilterClasse] = useState('')
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
  }, [debouncedSearch, filterClasse, filterStatut])

  const listParams = {
    ...(filterAnnee ? { id_annee_scolaire: Number(filterAnnee) } : {}),
    ...(filterClasse ? { id_classe: Number(filterClasse) } : {}),
    ...(filterStatut ? { statut: filterStatut } : {}),
  }

  const { data: inscriptions = [], isLoading, isFetching, isError } = useQuery({
    queryKey: ['inscriptions', filterAnnee, filterClasse, filterStatut, debouncedSearch, page],
    queryFn: () => fetchInscriptions({
      ...listParams,
      q: debouncedSearch,
      skip: (page - 1) * PAGE_SIZE,
      limit: PAGE_SIZE,
    }),
    enabled: !!filterAnnee,
  })

  const { data: total = 0 } = useQuery({
    queryKey: ['inscriptions', 'total', filterAnnee, filterClasse, filterStatut, debouncedSearch],
    queryFn: () => fetchInscriptionsTotal({ ...listParams, q: debouncedSearch }),
    enabled: !!filterAnnee,
  })

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE))

  useEffect(() => {
    if (page > totalPages) setPage(totalPages)
  }, [page, totalPages])

  const { data: statsTotal = 0 } = useQuery({
    queryKey: ['inscriptions', 'stats', 'total', filterAnnee, filterClasse],
    queryFn: () => fetchInscriptionsTotal({ ...(filterAnnee ? { id_annee_scolaire: Number(filterAnnee) } : {}), ...(filterClasse ? { id_classe: Number(filterClasse) } : {}) }),
    enabled: !!filterAnnee,
  })
  const { data: statsInscrits = 0 } = useQuery({
    queryKey: ['inscriptions', 'stats', 'inscrits', filterAnnee, filterClasse],
    queryFn: () => fetchInscriptionsTotal({ ...(filterAnnee ? { id_annee_scolaire: Number(filterAnnee) } : {}), ...(filterClasse ? { id_classe: Number(filterClasse) } : {}), statut: 'Inscrit' }),
    enabled: !!filterAnnee,
  })
  const { data: statsRedoublants = 0 } = useQuery({
    queryKey: ['inscriptions', 'stats', 'redoublants', filterAnnee, filterClasse],
    queryFn: () => fetchInscriptionsTotal({ ...(filterAnnee ? { id_annee_scolaire: Number(filterAnnee) } : {}), ...(filterClasse ? { id_classe: Number(filterClasse) } : {}), statut: 'Redoublant' }),
    enabled: !!filterAnnee,
  })
  const { data: statsExclus = 0 } = useQuery({
    queryKey: ['inscriptions', 'stats', 'exclus', filterAnnee, filterClasse],
    queryFn: () => fetchInscriptionsTotal({ ...(filterAnnee ? { id_annee_scolaire: Number(filterAnnee) } : {}), ...(filterClasse ? { id_classe: Number(filterClasse) } : {}), statut: 'Exclu' }),
    enabled: !!filterAnnee,
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
          <PageHeader
            title="Inscriptions"
            count={total}
            countLabel="inscription(s)"
            actionLabel={tab === 'liste' && canWrite ? 'Nouvelle inscription' : undefined}
            onAction={tab === 'liste' && canWrite ? () => setTab('nouvelle') : undefined}
          />
          {tab === 'nouvelle' && (
            <Button variant="secondary" onClick={() => setTab('liste')}>
              <ChevronLeft size={14} strokeWidth={1.75} className="mr-1.5" />
              Retour à la liste
            </Button>
          )}
        </div>

        <div className="flex gap-1 w-fit rounded-[var(--radius-sm)] bg-[var(--surface-2)] p-1">
          {(canWrite ? (['liste', 'nouvelle'] as Tab[]) : (['liste'] as Tab[])).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={clsx(
                'rounded-[var(--radius-sm)] px-4 py-1.5 text-sm font-medium transition-all',
                tab === t
                  ? 'bg-[var(--surface)] text-[var(--ink)] shadow-[var(--shadow-sm)]'
                  : 'bg-transparent text-[var(--ink-dim)] hover:text-[var(--ink)]',
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
                    <p className="text-sm font-medium text-[var(--ink-dim)]">{s.label}</p>
                    <p className="mt-3 text-3xl font-medium text-[var(--ink)]">{value}</p>
                  </Card>
                )
              })}
            </div>

            <PageToolbar>
              <ToolbarSearch
                placeholder="Rechercher"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                aria-label="Rechercher une inscription"
              />
              <ToolbarFilter value={filterClasse} onChange={(e) => setFilterClasse(e.target.value)} disabled={!classes.length} aria-label="Filtrer par classe">
                <option value="">Toutes les classes</option>
                {classes.map((c) => (
                  <option key={c.id} value={c.id}>{c.niveau} — {c.nom}</option>
                ))}
              </ToolbarFilter>
              <ToolbarFilter value={filterStatut} onChange={(e) => setFilterStatut(e.target.value)} aria-label="Filtrer par statut">
                <option value="">Tous les statuts</option>
                <option value="Inscrit">Inscrit</option>
                <option value="Redoublant">Redoublant</option>
                <option value="Transféré">Transféré</option>
                <option value="Exclu">Exclu</option>
              </ToolbarFilter>
            </PageToolbar>

            {isLoading ? (
              <TableSkeleton rows={8} />
            ) : isError ? (
              <div className="py-16">
                <EmptyState title="Erreur" message="Impossible de charger les inscriptions." />
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
                      <TableHead >Redoublement</TableHead>
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
                                <p className="text-sm text-[var(--ink)] group-hover:text-[var(--action-bright)]">{i.eleve_nom ?? '—'} {i.eleve_prenom ?? '—'}</p>
                              </div>
                            </Link>
                          </div>
                        </TableCell>
                        <TableCell className="text-[var(--ink-dim)]">
                          {annees.find((a) => a.id === i.id_annee_scolaire)?.libelle ?? '—'}
                        </TableCell>
                        <TableCell className="text-[var(--ink-dim)]">{formatDate(i.date_inscription)}</TableCell>
                        <TableCell>
                          <Badge tone={statutTone(i.statut)}>{i.statut}</Badge>
                        </TableCell>
                        <TableCell className="text-center text-[var(--ink-dim)]">
                          {i.nb_redoublements}
                        </TableCell>
                        <TableCell className="text-right">
                          {canDelete && (
                            <button
                              onClick={() => setDeleting(i)}
                              className="rounded-[var(--radius-sm)] p-1.5 text-[var(--ink-faint)] transition-colors hover:bg-[var(--danger-w)] hover:text-[var(--danger)]"
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
              canImport={true}
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
          try {
            await createInscription(data)
            toast('Élève inscrit')
            setDrawerOpen(false)
            qc.invalidateQueries({ queryKey: ['inscriptions'] })
          } catch (err) {
            toast(extractErrorMessage(err), 'error')
          }
        }}
      />
    </div>
  )
}
