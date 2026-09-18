import { useEffect, useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { UserCheck, UserX, Pencil, GraduationCap } from 'lucide-react'
import { Avatar } from '@/components/ui/Avatar'
import { Badge } from '@/components/ui/Badge'
import { EmptyState } from '@/components/ui/EmptyState'
import { PageHeader } from '@/components/ui/PageHeader'
import { PageToolbar, ToolbarSearch, ToolbarFilter } from '@/components/ui/PageToolbar'
import { Pagination } from '@/components/ui/Pagination'
import { TableSkeleton } from '@/components/ui/TableSkeleton'
import { Tooltip } from '@/components/ui/Tooltip'
import { Table, TableBody, TableCell, TableContainer, TableHead, TableHeader, TableRow } from '@/components/ui/Table'
import { toast } from '@/components/ui/toast'
import { extractErrorMessage } from '@/lib/api'
import { activerEleve, desactiverEleve, fetchEleves, fetchElevesTotal, updateEleve } from './api'
import { fetchClasses } from '@/features/classes/api'
import { createInscription } from '@/features/inscriptions/api'
import InscriptionFormDrawer from '@/features/inscriptions/InscriptionFormDrawer'
import InscriptionWizard from '@/features/inscriptions/InscriptionWizard'
import { useLectureSeule } from '@/features/annees_scolaires/useLectureSeule'
import { EleveFormDrawer } from './EleveFormDrawer'
import type { Eleve } from './types'

const PAGE_SIZE = 50

export default function EleveListPage() {
  const { lectureSeule } = useLectureSeule()
  const canWrite = !lectureSeule
  const queryClient = useQueryClient()

  const [search, setSearch] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [filterClasse, setFilterClasse] = useState('')
  const [filterStatut, setFilterStatut] = useState('')
  const [page, setPage] = useState(1)

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(search.trim()), 300)
    return () => clearTimeout(timer)
  }, [search])

  useEffect(() => {
    setPage(1)
  }, [debouncedSearch, filterClasse, filterStatut])

  const { data: classes = [] } = useQuery({ queryKey: ['classes'], queryFn: fetchClasses })

  const { data: eleves = [], isLoading, isFetching, isError } = useQuery({
    queryKey: ['eleves', 'liste', page, debouncedSearch, filterClasse, filterStatut],
    queryFn: () => fetchEleves({
      skip: (page - 1) * PAGE_SIZE,
      limit: PAGE_SIZE,
      q: debouncedSearch,
      classe_id: filterClasse ? Number(filterClasse) : undefined,
      statut: filterStatut || undefined,
    }),
  })

  const { data: total = 0 } = useQuery({
    queryKey: ['eleves', 'total', debouncedSearch, filterClasse, filterStatut],
    queryFn: () => fetchElevesTotal(debouncedSearch, {
      classe_id: filterClasse ? Number(filterClasse) : undefined,
      statut: filterStatut || undefined,
    }),
  })

  const totalPages = useMemo(() => Math.max(1, Math.ceil(total / PAGE_SIZE)), [total])

  useEffect(() => {
    if (page > totalPages) setPage(totalPages)
  }, [page, totalPages])

  const [showWizard, setShowWizard] = useState(false)
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [editing, setEditing] = useState<Eleve | null>(null)
  const [inscriptionOpen, setInscriptionOpen] = useState(false)
  const [inscriptionMatricule, setInscriptionMatricule] = useState('')

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['eleves'] })
    queryClient.invalidateQueries({ queryKey: ['inscriptions'] })
  }

  const updateMutation = useMutation({
    mutationFn: ({ matricule, payload }: { matricule: string; payload: Parameters<typeof updateEleve>[1] }) =>
      updateEleve(matricule, payload),
    onSuccess: () => { toast('Élève mis à jour'); invalidate() },
    onError: (e) => toast(extractErrorMessage(e), 'error'),
  })
  const activerMutation = useMutation({
    mutationFn: activerEleve,
    onSuccess: () => { toast('Élève activé'); invalidate() },
    onError: (e) => toast(extractErrorMessage(e), 'error'),
  })
  const desactiverMutation = useMutation({
    mutationFn: desactiverEleve,
    onSuccess: () => { toast('Élève désactivé'); invalidate() },
    onError: (e) => toast(extractErrorMessage(e), 'error'),
  })

  function openEdit(eleve: Eleve) {
    setEditing(eleve)
    setDrawerOpen(true)
  }

  return (
    <div className="w-full">
      <div className="flex flex-col gap-[10px]">
          <PageHeader
            title="Élèves"
            count={total}
            countLabel={`élève${total > 1 ? 's' : ''} enregistré${total > 1 ? 's' : ''}`}
            actionLabel={!showWizard && canWrite ? 'Nouvelle inscription' : undefined}
            onAction={!showWizard && canWrite ? () => setShowWizard(true) : undefined}
          />

        {showWizard ? (
          <InscriptionWizard
            onComplete={() => {
              invalidate()
              queryClient.invalidateQueries({ queryKey: ['tuteurs'] })
              setShowWizard(false)
            }}
            onCancel={() => setShowWizard(false)}
            canImport={true}
          />
        ) : (
        <>
          <PageToolbar>
            <ToolbarSearch
              placeholder="Rechercher un élève…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              aria-label="Rechercher un élève"
            />
            <ToolbarFilter
              value={filterClasse}
              onChange={(e) => setFilterClasse(e.target.value)}
              aria-label="Filtrer par classe"
            >
              <option value="">Toutes les classes</option>
              {classes.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.niveau} — {c.nom}
                </option>
              ))}
            </ToolbarFilter>
            <ToolbarFilter
              value={filterStatut}
              onChange={(e) => setFilterStatut(e.target.value)}
              aria-label="Filtrer par statut"
            >
              <option value="">Tous les statuts</option>
              <option value="actif">Actif</option>
              <option value="inactif">Inactif</option>
            </ToolbarFilter>
            <span className="ml-2 text-[11.5px] text-[var(--ink-faint)]">
              {total} élève{total > 1 ? 's' : ''}
            </span>
          </PageToolbar>

        {isLoading ? (
          <TableSkeleton rows={8} />
        ) : isError ? (
          <div className="py-16">
            <EmptyState title="Erreur" message="Impossible de charger la liste des élèves." />
          </div>
        ) : eleves.length === 0 ? (
          <div className="py-16">
            <EmptyState message={debouncedSearch ? 'Aucun élève ne correspond à cette recherche.' : 'Aucun élève enregistré pour le moment.'} />
          </div>
        ) : (
          <TableContainer>
            <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Élève</TableHead>
                <TableHead>Matricule</TableHead>
                <TableHead>Classe</TableHead>
                <TableHead>Tuteur</TableHead>
                <TableHead>Statut</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {eleves.map((eleve) => (
                <TableRow key={eleve.matricule} className="group">
                  <TableCell>
                    <Link to={`/app/eleves/${eleve.matricule}`} className="flex items-center gap-3 group">
                      <Avatar nom={eleve.nom} prenom={eleve.prenom} photo={eleve.photo} size="sm" />
                      <span className="font-medium text-[var(--color-ink)] group-hover:text-[var(--color-action-bright)]">
                        {eleve.prenom} {eleve.nom}
                      </span>
                    </Link>
                  </TableCell>
                  <TableCell className="font-[var(--font-mono)] text-xs text-[var(--color-ink-dim)]">{eleve.matricule}</TableCell>
                  <TableCell className="text-[var(--color-ink-dim)]">
                    {eleve.classe ? `${eleve.classe.niveau} — ${eleve.classe.nom}` : <span className="text-[var(--color-ink-faint)]">Non affecté</span>}
                  </TableCell>
                  <TableCell className="text-[var(--color-ink-dim)]">
                    {eleve.tuteur.prenom} {eleve.tuteur.nom}
                  </TableCell>
                  <TableCell>
                    <Badge tone={eleve.statut === 'actif' ? 'success' : 'neutral'}>
                      {eleve.statut === 'actif' ? 'Actif' : 'Inactif'}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center justify-end gap-1 opacity-0 transition-all group-hover:opacity-100">
                      {canWrite && (
                        <>
                          {!eleve.classe && (
                            <Tooltip content="Inscrire">
                            <button
                              onClick={() => { setInscriptionMatricule(eleve.matricule); setInscriptionOpen(true) }}
                              aria-label="Inscrire"
                              className="rounded-[var(--radius-sm)] p-1.5 text-[var(--color-ink-faint)] transition-colors hover:bg-[var(--color-action-wash)] hover:text-[var(--color-action-bright)]"
                            >
                              <GraduationCap strokeWidth={1.75} className="size-4" />
                            </button>
                            </Tooltip>
                          )}
                          <Tooltip content="Modifier">
                          <button
                            onClick={() => openEdit(eleve)}
                            aria-label="Modifier"
                            className="rounded-[var(--radius-sm)] p-1.5 text-[var(--color-ink-faint)] transition-colors hover:bg-[var(--color-surface-3)] hover:text-[var(--color-ink)]"
                          >
                            <Pencil strokeWidth={1.75} className="size-4" />
                          </button>
                          </Tooltip>
                          {eleve.statut === 'actif' ? (
                            <Tooltip content="Désactiver">
                            <button
                              onClick={() => desactiverMutation.mutate(eleve.matricule)}
                              aria-label="Désactiver"
                              className="rounded-[var(--radius-sm)] p-1.5 text-[var(--color-ink-faint)] transition-colors hover:bg-[var(--color-danger-wash)] hover:text-[var(--color-danger)]"
                            >
                              <UserX strokeWidth={1.75} className="size-4" />
                            </button>
                            </Tooltip>
                          ) : (
                            <Tooltip content="Activer">
                            <button
                              onClick={() => activerMutation.mutate(eleve.matricule)}
                              aria-label="Activer"
                              className="rounded-[var(--radius-sm)] p-1.5 text-[var(--color-ink-faint)] transition-colors hover:bg-[var(--color-success-wash)] hover:text-[var(--color-success)]"
                            >
                              <UserCheck strokeWidth={1.75} className="size-4" />
                            </button>
                            </Tooltip>
                          )}
                        </>
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
        </>
        )}

      <EleveFormDrawer
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        eleve={editing}
        onCreate={async () => {
          throw new Error('La création d’un élève passe par une inscription.')
        }}
        onUpdate={(matricule, payload) => updateMutation.mutateAsync({ matricule, payload })}
        canImport={true}
      />

      <InscriptionFormDrawer
        open={inscriptionOpen}
        onClose={() => setInscriptionOpen(false)}
        initialMatricule={inscriptionMatricule}
        onSubmit={async (data) => {
          await createInscription(data)
          toast('Élève inscrit')
          setInscriptionOpen(false)
          invalidate()
        }}
      />
      </div>
    </div>
  )
}
