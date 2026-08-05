import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Plus, Check } from 'lucide-react'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { EmptyState } from '@/components/ui/EmptyState'
import { Input } from '@/components/ui/Input'
import { Pagination } from '@/components/ui/Pagination'
import { SearchInput } from '@/components/ui/SearchInput'
import { TableSkeleton } from '@/components/ui/TableSkeleton'
import { toast } from '@/components/ui/toast'
import { extractErrorMessage } from '@/lib/api'
import { useAuth } from '@/auth/useAuth'
import { formatDate } from '@/lib/format'
import { fetchAbsences, fetchAbsencesTotal, createAbsence, justifierAbsence } from './api'
import AbsenceFormDrawer from './AbsenceFormDrawer'
import type { AbsenceCreateInput } from './types'

const PAGE_SIZE = 50

const justifieeParam = (f: 'tous' | 'justifiees' | 'non-justifiees'): boolean | undefined => {
  if (f === 'justifiees') return true
  if (f === 'non-justifiees') return false
  return undefined
}

export default function AbsenceListPage() {
  const { user } = useAuth()
  const canWrite = user?.role === 'admin' || user?.role === 'directeur'
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
    queryKey: ['absences', 'total'],
    queryFn: () => fetchAbsencesTotal(),
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
      <div className="flex flex-col gap-5">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-2xl font-semibold tracking-tight text-[var(--color-ink)]">
              Absences
            </h2>
            <p className="mt-1 text-sm text-[var(--color-ink-dim)]">
              Suivi des absences et justifications
            </p>
          </div>
          {canWrite && <Button variant="primary" onClick={() => setDrawerOpen(true)}>
            <Plus size={16} strokeWidth={1.75} className="mr-1.5" />
            Nouvelle absence
          </Button>}
        </div>

        <div className="grid grid-cols-2 gap-4 sm:grid-cols-2">
          <Card>
            <div className="px-5 pt-5">
              <p className="font-[var(--font-mono)] text-xs uppercase tracking-wider text-[var(--color-ink-faint)]">Total absences</p>
            </div>
            <div className="px-5 pb-5 pt-2">
              <p className="text-2xl font-semibold text-[var(--color-ink)]">{stats.total}</p>
            </div>
          </Card>
          <Card>
            <div className="px-5 pt-5">
              <p className="font-[var(--font-mono)] text-xs uppercase tracking-wider text-[var(--color-ink-faint)]">Non justifiées</p>
            </div>
            <div className="px-5 pb-5 pt-2">
              <p className="text-2xl font-semibold text-[var(--color-warning)]">{stats.nonJust}</p>
            </div>
          </Card>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <SearchInput
            className="flex-1"
            placeholder="Rechercher un élève, cours…"
            value={search}
            onChange={setSearch}
          />
          <div className="flex gap-1.5">
            {(['tous', 'justifiees', 'non-justifiees'] as const).map((f) => (
              <button
                key={f}
                onClick={() => setFilterJustifiee(f)}
                className={`rounded-full px-4 py-1.5 text-xs font-medium transition-colors ${
                  filterJustifiee === f
                    ? f === 'tous' ? 'bg-[var(--color-brand)] text-[var(--color-surface)]'
                    : f === 'justifiees' ? 'bg-[var(--color-success)] text-[var(--color-surface)]'
                    : 'bg-[var(--color-warning)] text-[var(--color-surface)]'
                    : 'bg-[var(--color-surface-2)] text-[var(--color-ink-dim)] hover:bg-[var(--color-surface-3)] hover:text-[var(--color-ink)]'
                }`}
              >
                {f === 'tous' ? 'Toutes' : f === 'justifiees' ? 'Justifiées' : 'Non justifiées'}
              </button>
            ))}
          </div>
        </div>

        {isLoading ? (
          <TableSkeleton rows={8} />
        ) : isError ? (
          <div className="py-16">
            <EmptyState message="Impossible de charger les absences." />
          </div>
        ) : absences.length === 0 ? (
          <div className="py-16">
            <EmptyState message="Aucune absence trouvée." />
          </div>
        ) : (
          <Card className="overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[var(--color-border-soft)] text-xs font-[var(--font-mono)] text-[var(--color-ink-faint)]">
                  <th className="px-5 py-3 text-left font-medium">Élève</th>
                  <th className="px-5 py-3 text-left font-medium">Classe</th>
                  <th className="px-5 py-3 text-left font-medium">Cours</th>
                  <th className="px-5 py-3 text-left font-medium">Date</th>
                  <th className="px-5 py-3 text-center font-medium">Statut</th>
                  <th className="px-5 py-3 text-left font-medium">Motif</th>
                  <th className="px-5 py-3 text-right font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {absences.map((a) => (
                  <tr
                    key={a.id}
                    className="border-b border-[var(--color-border-soft)] last:border-0 hover:bg-[var(--color-surface-2)]"
                  >
                    <td className="px-5 py-3 text-[var(--color-ink)]">
                      {a.eleve ? (
                        <Link to={`/app/eleves/${a.matricule_eleve}`} className="hover:text-[var(--color-brand-bright)]">
                          {a.eleve.prenom} {a.eleve.nom}
                        </Link>
                      ) : (
                        <span className="text-[var(--color-ink-faint)]">—</span>
                      )}
                    </td>
                    <td className="px-5 py-3 text-[var(--color-ink-dim)]">
                      {a.eleve?.classe ? `${a.eleve.classe.niveau} ${a.eleve.classe.nom}` : '—'}
                    </td>
                    <td className="px-5 py-3 text-[var(--color-ink-dim)]">{a.cours?.nom ?? '—'}</td>
                    <td className="px-5 py-3 text-[var(--color-ink-dim)]">{formatDate(a.date_absence)}</td>
                    <td className="px-5 py-3 text-center">
                      {a.justifiee ? (
                        <Badge tone="success">Justifiée</Badge>
                      ) : (
                        <Badge tone="danger">Non justifiée</Badge>
                      )}
                    </td>
                    <td className="px-5 py-3 text-[var(--color-ink-dim)]">{a.motif ?? '—'}</td>
                    <td className="px-5 py-3 text-right">
                      {!a.justifiee && canWrite && (
                        <button
                          onClick={() => setJustifying({ id: a.id, label: `${a.eleve?.prenom} ${a.eleve?.nom}` })}
                          className="rounded-[var(--radius-sm)] p-1.5 text-[var(--color-ink-faint)] transition-colors hover:bg-[var(--color-success-wash)] hover:text-[var(--color-success)]"
                          aria-label={`Justifier l'absence de ${a.eleve?.prenom} ${a.eleve?.nom}`}
                        >
                          <Check size={14} strokeWidth={1.75} />
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
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
