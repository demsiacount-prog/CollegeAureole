import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Check } from 'lucide-react'
import { Badge } from '@/components/ui/Badge'
import { Card } from '@/components/ui/Card'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { EmptyState } from '@/components/ui/EmptyState'
import { Input } from '@/components/ui/Input'
import { Pagination } from '@/components/ui/Pagination'
import { PageHeader } from '@/components/ui/PageHeader'
import { PageToolbar, ToolbarSearch } from '@/components/ui/PageToolbar'
import { TableSkeleton } from '@/components/ui/TableSkeleton'
import { Table, TableBody, TableCell, TableContainer, TableHead, TableHeader, TableRow } from '@/components/ui/Table'
import { toast } from '@/components/ui/toast'
import { extractErrorMessage } from '@/lib/api'
import { formatDate } from '@/lib/format'
import { fetchAbsences, fetchAbsencesTotal, createAbsence, justifierAbsence } from './api'
import AbsenceFormDrawer from './AbsenceFormDrawer'
import { useLectureSeule } from '@/features/annees_scolaires/useLectureSeule'
import type { AbsenceCreateInput } from './types'

const PAGE_SIZE = 50

const justifieeParam = (f: 'tous' | 'justifiees' | 'non-justifiees'): boolean | undefined => {
  if (f === 'justifiees') return true
  if (f === 'non-justifiees') return false
  return undefined
}

export default function AbsenceListPage() {
  const { lectureSeule } = useLectureSeule()
  const canWrite = !lectureSeule
  const qc = useQueryClient()

  const [search, setSearch] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [filterJustifiee, setFilterJustifiee] = useState<'tous' | 'justifiees' | 'non-justifiees'>('tous')
  const [page, setPage] = useState(1)

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(search.trim()), 300)
    return () => clearTimeout(timer)
  }, [search])

  useEffect(() => {
    setPage(1)
  }, [debouncedSearch, filterJustifiee])

  const { data: absences = [], isLoading, isFetching, isError } = useQuery({
    queryKey: ['absences', 'liste', page, debouncedSearch, filterJustifiee],
    queryFn: () => fetchAbsences({
      skip: (page - 1) * PAGE_SIZE,
      limit: PAGE_SIZE,
      q: debouncedSearch,
      justifiee: justifieeParam(filterJustifiee),
    }),
  })

  const { data: total = 0 } = useQuery({
    queryKey: ['absences', 'total', debouncedSearch, filterJustifiee],
    queryFn: () =>
      fetchAbsencesTotal({
        q: debouncedSearch,
        justifiee: justifieeParam(filterJustifiee),
      }),
  })

  const { data: totalNonJustifiees = 0 } = useQuery({
    queryKey: ['absences', 'total', 'non-justifiees'],
    queryFn: () => fetchAbsencesTotal({ justifiee: false }),
  })

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE))

  useEffect(() => {
    if (page > totalPages) setPage(totalPages)
  }, [page, totalPages])

  const [drawerOpen, setDrawerOpen] = useState(false)
  const [justifying, setJustifying] = useState<{ id: number; label: string } | null>(null)
  const [justifierMotif, setJustifierMotif] = useState('')

  const createMut = useMutation({
    mutationFn: (data: AbsenceCreateInput) => createAbsence(data),
    onSuccess: () => { toast('Absence enregistrée'); qc.invalidateQueries({ queryKey: ['absences'] }); setDrawerOpen(false) },
    onError: (e) => toast(extractErrorMessage(e), 'error'),
  })

  const justifierMut = useMutation({
    mutationFn: ({ id, motif }: { id: number; motif: string }) =>
      justifierAbsence(id, { justifiee: true, motif: motif || null }),
    onSuccess: () => { toast('Absence justifiée'); qc.invalidateQueries({ queryKey: ['absences'] }); setJustifying(null); setJustifierMotif('') },
    onError: (e) => toast(extractErrorMessage(e), 'error'),
  })

  const stats = { total, nonJust: totalNonJustifiees }

  return (
    <div className="w-full">
      <div className="flex flex-col gap-[10px]">
        <PageHeader
          title="Absences"
          subtitle={<p className="mt-1 text-sm text-[var(--color-ink-dim)]">Suivi des absences et justifications</p>}
          actionLabel={canWrite ? 'Nouvelle absence' : undefined}
          onAction={canWrite ? () => setDrawerOpen(true) : undefined}
        />

        <div className="grid grid-cols-2 gap-3 sm:grid-cols-2">
          <Card className="flex flex-col justify-between border-t-2 p-3.5" style={{ borderTopColor: 'var(--color-mod-ress)' }}>
            <p className="text-[10.5px] font-medium uppercase tracking-[0.06em] text-[var(--color-ink-faint)]">Total absences</p>
            <p className="mt-1 text-[26px] font-bold leading-none text-[var(--color-ink)]">{stats.total}</p>
          </Card>
          <Card className="flex flex-col justify-between border-t-2 p-3.5" style={{ borderTopColor: 'var(--color-warning)' }}>
            <p className="text-[10.5px] font-medium uppercase tracking-[0.06em] text-[var(--color-ink-faint)]">Non justifiées</p>
            <p className="mt-1 text-[26px] font-bold leading-none text-[var(--color-warning)]">{stats.nonJust}</p>
          </Card>
        </div>

        <PageToolbar>
          <ToolbarSearch
            placeholder="Rechercher"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            aria-label="Rechercher un élève"
          />
          <div className="flex h-[30px] shrink-0 items-center gap-1 rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] p-1">
            {(['tous', 'justifiees', 'non-justifiees'] as const).map((f) => {
              const active = filterJustifiee === f
              return (
                <button
                  key={f}
                  onClick={() => setFilterJustifiee(f)}
                  className={`h-full rounded-[var(--radius-sm)] px-2.5 text-[11.5px] font-medium transition-colors ${
                    active
                      ? 'bg-[var(--surface-3)] text-[var(--ink)]'
                      : 'bg-transparent text-[var(--ink-faint)] hover:text-[var(--ink)]'
                  }`}
                >
                  {f === 'tous' ? 'Toutes' : f === 'justifiees' ? 'Justifiées' : 'Non justifiées'}
                </button>
              )
            })}
          </div>
        </PageToolbar>

        {isLoading ? (
          <TableSkeleton rows={8} />
        ) : isError ? (
          <div className="py-16">
            <EmptyState title="Erreur" message="Impossible de charger les absences." />
          </div>
        ) : absences.length === 0 ? (
          <div className="py-16">
            <EmptyState message="Aucune absence trouvée." />
          </div>
        ) : (
          <TableContainer>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Élève</TableHead>
                  <TableHead>Classe</TableHead>
                  <TableHead>Cours</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead className="text-center">Statut</TableHead>
                  <TableHead>Motif</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {absences.map((a) => (
                  <TableRow key={a.id}>
                    <TableCell className="text-[var(--color-ink)]">
                      {a.eleve ? (
                        <Link to={`/app/eleves/${a.matricule_eleve}`} className="hover:text-[var(--color-action-bright)]">
                          {a.eleve.prenom} {a.eleve.nom}
                        </Link>
                      ) : (
                        <span className="text-[var(--color-ink-faint)]">—</span>
                      )}
                    </TableCell>
                    <TableCell className="text-[var(--color-ink-dim)]">
                      {a.eleve?.classe ? `${a.eleve.classe.niveau} ${a.eleve.classe.nom}` : '—'}
                    </TableCell>
                    <TableCell className="text-[var(--color-ink-dim)]">{a.cours?.nom ?? '—'}</TableCell>
                    <TableCell className="text-[var(--color-ink-dim)]">{formatDate(a.date_absence)}</TableCell>
                    <TableCell className="text-center">
                      {a.justifiee ? (
                        <Badge tone="success">Justifiée</Badge>
                      ) : (
                        <Badge tone="danger">Non justifiée</Badge>
                      )}
                    </TableCell>
                    <TableCell className="text-[var(--color-ink-dim)]">{a.motif ?? '—'}</TableCell>
                    <TableCell className="text-right">
                      {!a.justifiee && canWrite && (
                        <button
                          onClick={() => setJustifying({ id: a.id, label: `${a.eleve?.prenom} ${a.eleve?.nom}` })}
                          className="rounded-[var(--radius-sm)] p-1.5 text-[var(--color-ink-faint)] transition-colors hover:bg-[var(--color-success-wash)] hover:text-[var(--color-success)]"
                          aria-label={`Justifier l'absence de ${a.eleve?.prenom} ${a.eleve?.nom}`}
                        >
                          <Check size={14} strokeWidth={1.75} />
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
      </div>

      <AbsenceFormDrawer
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        onSubmit={(data) => createMut.mutate(data)}
      />

      <ConfirmDialog
        open={!!justifying}
        onClose={() => { setJustifying(null); setJustifierMotif('') }}
        onConfirm={() => { if (justifying) justifierMut.mutate({ id: justifying.id, motif: justifierMotif }) }}
        title="Justifier cette absence ?"
        description={justifying ? `Absence de ${justifying.label}. Ajoutez un motif (optionnel).` : ''}
        confirmLabel="Justifier"
        variant="success"
      >
        <Input label="Motif" value={justifierMotif} onChange={(e) => setJustifierMotif(e.target.value)} placeholder="Motif de la justification" />
      </ConfirmDialog>
    </div>
  )
}
