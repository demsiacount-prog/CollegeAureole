import { useEffect, useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Plus, Pencil, Trash2, LayoutGrid, List as ListIcon, MapPin } from 'lucide-react'
import { Card, CardBody } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Select } from '@/components/ui/Select'
import { TableSkeleton } from '@/components/ui/TableSkeleton'
import { EmptyState } from '@/components/ui/EmptyState'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { toast } from '@/components/ui/toast'
import { extractErrorMessage } from '@/lib/api'
import { scheduleDeleteWithUndo } from '@/lib/undoDelete'
import { useAuth } from '@/auth/useAuth'
import { fetchAnneesScolaires } from '@/features/annees_scolaires/api'
import { fetchClasses } from '@/features/classes/api'
import { fetchEnseignants } from '@/features/enseignants/api'
import { fetchSeances, createSeance, updateSeance, deleteSeance } from './api'
import SeanceFormDrawer from './SeanceFormDrawer'
import type { SeanceDetail, SeanceCreateInput } from './types'

const JOURS = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi']

function hhmm(t: string) {
  return t?.slice(0, 5) ?? ''
}



export default function SeanceListPage() {
  const { user } = useAuth()
  const canWrite = user?.role === 'admin' || user?.role === 'directeur'
  const canDelete = user?.role === 'admin'
  const qc = useQueryClient()

  const { data: annees = [] } = useQuery({ queryKey: ['annees-scolaires'], queryFn: fetchAnneesScolaires })
  const { data: classes = [] } = useQuery({ queryKey: ['classes'], queryFn: fetchClasses })
  const { data: enseignants = [] } = useQuery({ queryKey: ['enseignants'], queryFn: () => fetchEnseignants() })

  const [filterAnnee, setFilterAnnee] = useState('')
  useEffect(() => {
    if (!filterAnnee && annees.length > 0) {
      const active = annees.find((a) => a.active) ?? annees[0]
      setFilterAnnee(active.id.toString())
    }
  }, [annees, filterAnnee])
  const [filterClasse, setFilterClasse] = useState('')
  const [filterEnseignant, setFilterEnseignant] = useState('')
  const [vue, setVue] = useState<'grille' | 'liste'>('grille')

  const { data: seances = [], isLoading, isError } = useQuery({
    queryKey: ['seances', filterAnnee],
    queryFn: () => fetchSeances(Number(filterAnnee)),
    enabled: !!filterAnnee,
  })

  const [drawerOpen, setDrawerOpen] = useState(false)
  const [editing, setEditing] = useState<SeanceDetail | null>(null)
  const [deleting, setDeleting] = useState<SeanceDetail | null>(null)

  const createMut = useMutation({
    mutationFn: (data: SeanceCreateInput) => createSeance(data),
    onSuccess: () => { toast('Séance créée'); qc.invalidateQueries({ queryKey: ['seances'] }); setDrawerOpen(false); setEditing(null) },
    onError: (e) => toast(extractErrorMessage(e), 'error'),
  })

  const updateMut = useMutation({
    mutationFn: ({ id, data }: { id: number; data: SeanceCreateInput }) => updateSeance(id, data),
    onSuccess: () => { toast('Séance modifiée'); qc.invalidateQueries({ queryKey: ['seances'] }); setDrawerOpen(false); setEditing(null) },
    onError: (e) => toast(extractErrorMessage(e), 'error'),
  })

  const deleteMut = useMutation({
    mutationFn: deleteSeance,
    onSuccess: () => { toast('Séance supprimée'); qc.invalidateQueries({ queryKey: ['seances'] }); setDeleting(null) },
    onError: (e) => toast(extractErrorMessage(e), 'error'),
  })

  function handleOpenNew() {
    setEditing(null)
    setDrawerOpen(true)
  }

  function handleEdit(s: SeanceDetail) {
    setEditing(s)
    setDrawerOpen(true)
  }

  function handleFormSubmit(data: SeanceCreateInput) {
    if (editing) {
      updateMut.mutate({ id: editing.id, data })
    } else {
      createMut.mutate(data)
    }
  }

  const filtered = useMemo(() => {
    return seances.filter((s) => {
      if (filterClasse && s.id_classe !== Number(filterClasse)) return false
      if (filterEnseignant && s.cours?.enseignant?.matricule !== filterEnseignant) return false
      return true
    })
  }, [seances, filterClasse, filterEnseignant])

  const sorted = useMemo(
    () =>
      [...filtered].sort((a, b) => {
        const ja = JOURS.indexOf(a.jour_semaine)
        const jb = JOURS.indexOf(b.jour_semaine)
        if (ja !== jb) return ja - jb
        return a.heure_debut.localeCompare(b.heure_debut)
      }),
    [filtered],
  )

  // Les créneaux ne sont pas figés dans le modèle : on déduit la liste des
  // horaires réellement utilisés plutôt que d'en imposer un fixe.
  const creneaux = useMemo(() => {
    const set = new Map<string, { debut: string; fin: string }>()
    for (const s of filtered) {
      const key = `${s.heure_debut}-${s.heure_fin}`
      if (!set.has(key)) set.set(key, { debut: s.heure_debut, fin: s.heure_fin })
    }
    return [...set.values()].sort((a, b) => a.debut.localeCompare(b.debut))
  }, [filtered])

  function seancesDansCase(jour: string, debut: string) {
    return filtered.filter((s) => s.jour_semaine === jour && s.heure_debut === debut)
  }

  return (
    <div className="w-full">
      <div className="flex flex-col gap-5">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-2xl font-semibold tracking-tight text-[var(--color-ink)]">
              Emploi du temps
            </h2>
            <p className="mt-1 text-sm text-[var(--color-ink-dim)]">
              {filtered.length} séance{filtered.length > 1 ? 's' : ''}
              {filterClasse && classes.find((c) => c.id === Number(filterClasse)) && (
                <> — {classes.find((c) => c.id === Number(filterClasse))?.niveau} {classes.find((c) => c.id === Number(filterClasse))?.nom}</>
              )}
              {filterEnseignant && enseignants.find((e) => e.matricule === filterEnseignant) && (
                <> — {enseignants.find((e) => e.matricule === filterEnseignant)?.prenom} {enseignants.find((e) => e.matricule === filterEnseignant)?.nom}</>
              )}
            </p>
          </div>
          {canWrite && (
            <Button variant="primary" onClick={handleOpenNew}>
              <Plus size={16} strokeWidth={1.75} className="mr-1.5" />
              Nouvelle séance
            </Button>
          )}
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <Select value={filterAnnee} onChange={(e) => setFilterAnnee(e.target.value)} className="w-48">
            {!annees.length && <option value="">—</option>}
            {annees.map((a) => (
              <option key={a.id} value={a.id}>{a.libelle}</option>
            ))}
          </Select>
          <Select
            value={filterClasse}
            onChange={(e) => { setFilterClasse(e.target.value); setFilterEnseignant('') }}
            className="w-48"
          >
            <option value="">Toutes les classes</option>
            {classes.map((c) => (
              <option key={c.id} value={c.id}>{c.niveau} — {c.nom}</option>
            ))}
          </Select>
          <Select
            value={filterEnseignant}
            onChange={(e) => { setFilterEnseignant(e.target.value); setFilterClasse('') }}
            className="w-52"
          >
            <option value="">Tous les enseignants</option>
            {enseignants.map((e) => (
              <option key={e.matricule} value={e.matricule}>{e.prenom} {e.nom}</option>
            ))}
          </Select>

          <div className="ml-auto flex gap-1 rounded-[var(--radius-sm)] border border-[var(--color-border)] p-0.5">
            <button
              onClick={() => setVue('grille')}
              className={`flex items-center gap-1.5 rounded-[4px] px-2.5 py-1.5 text-xs font-medium transition-colors ${vue === 'grille' ? 'bg-[var(--color-surface-3)] text-[var(--color-ink)]' : 'text-[var(--color-ink-faint)]'}`}
            >
              <LayoutGrid size={13} strokeWidth={1.75} /> Grille
            </button>
            <button
              onClick={() => setVue('liste')}
              className={`flex items-center gap-1.5 rounded-[4px] px-2.5 py-1.5 text-xs font-medium transition-colors ${vue === 'liste' ? 'bg-[var(--color-surface-3)] text-[var(--color-ink)]' : 'text-[var(--color-ink-faint)]'}`}
            >
              <ListIcon size={13} strokeWidth={1.75} /> Liste
            </button>
          </div>
        </div>

        {!filterClasse && !filterEnseignant ? (
          <div className="py-16">
            <EmptyState message="Sélectionnez une classe ou un enseignant pour voir l'emploi du temps." />
          </div>
        ) : isLoading ? (
          <TableSkeleton rows={8} />
        ) : isError ? (
          <div className="py-16">
            <EmptyState message="Impossible de charger les séances." />
          </div>
        ) : filtered.length === 0 ? (
          <div className="py-16">
            <EmptyState message="Aucune séance pour ce filtre." />
          </div>
        ) : vue === 'grille' ? (
          <div className="overflow-x-auto rounded-[var(--radius-lg)] border border-[var(--color-border)]">
            <table className="w-full border-collapse text-sm">
              <thead>
                <tr>
                  <th className="w-28 border-b border-r border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-3 text-left text-xs font-medium text-[var(--color-ink-faint)]">
                    Horaire
                  </th>
                  {JOURS.map((j) => (
                    <th key={j} className="border-b border-r border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-3 text-center text-xs font-semibold text-[var(--color-ink)] last:border-r-0">
                      {j}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {creneaux.map((cr) => (
                  <tr key={cr.debut}>
                    <td className="border-b border-r border-[var(--color-border)] px-3 py-2 align-top font-[var(--font-mono)] text-xs text-[var(--color-ink-dim)]">
                      {hhmm(cr.debut)}<br />{hhmm(cr.fin)}
                    </td>
                    {JOURS.map((jour) => {
                      const cases = seancesDansCase(jour, cr.debut)
                      return (
                        <td key={jour} className="min-w-[180px] border-b border-r border-[var(--color-border)] p-2 align-top last:border-r-0">
                          <div className="flex flex-col gap-1.5">
                            {cases.map((s) => (
                                <div
                                  key={s.id}
                                  className="group relative flex-1 rounded-[var(--radius-sm)] border border-[var(--color-border-soft)] bg-[var(--color-surface)] px-3 py-2"
                                >
                                  <p className="text-xs font-semibold leading-tight text-[var(--color-ink)]">
                                    {s.cours?.nom ?? '—'}
                                  </p>
                                  {!filterClasse && s.classe && (
                                    <p className="mt-0.5 text-[11px] text-[var(--color-ink-dim)]">{s.classe.niveau} {s.classe.nom}</p>
                                  )}
                                  {!filterEnseignant && s.cours?.enseignant && (
                                    <p className="text-[11px] text-[var(--color-ink-dim)]">{s.cours.enseignant.prenom} {s.cours.enseignant.nom}</p>
                                  )}
                                  {s.salle && (
                                    <p className="mt-0.5 flex items-center gap-1 text-[10px] text-[var(--color-ink-faint)]">
                                      <MapPin size={9} strokeWidth={1.75} /> {s.salle.nom}
                                    </p>
                                  )}
                                  {canWrite && (
                                    <div className="absolute right-1 top-1 hidden gap-0.5 group-hover:flex">
                                      <button
                                        onClick={() => handleEdit(s)}
                                        aria-label="Modifier"
                                        className="rounded-[var(--radius-sm)] bg-[var(--color-surface)] p-1 text-[var(--color-ink-dim)] shadow-sm transition-colors hover:bg-[var(--color-surface-3)] hover:text-[var(--color-ink)]"
                                      >
                                        <Pencil size={12} strokeWidth={1.75} />
                                      </button>
                                      {canDelete && (
                                        <button
                                          onClick={() => setDeleting(s)}
                                          aria-label="Supprimer"
                                          className="rounded-[var(--radius-sm)] bg-[var(--color-surface)] p-1 text-[var(--color-ink-dim)] shadow-sm transition-colors hover:bg-[var(--color-danger-wash)] hover:text-[var(--color-danger)]"
                                        >
                                          <Trash2 size={12} strokeWidth={1.75} />
                                        </button>
                                      )}
                                    </div>
                                  )}
                                </div>
                              ))}
                          </div>
                        </td>
                      )
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <Card>
            <CardBody>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-[var(--color-border)]">
                      <th className="pb-3 text-left font-medium text-[var(--color-ink-dim)]">Jour</th>
                      <th className="pb-3 text-left font-medium text-[var(--color-ink-dim)]">Horaire</th>
                      <th className="pb-3 text-left font-medium text-[var(--color-ink-dim)]">Cours</th>
                      <th className="pb-3 text-left font-medium text-[var(--color-ink-dim)]">Enseignant</th>
                      <th className="pb-3 text-left font-medium text-[var(--color-ink-dim)]">Classe</th>
                      <th className="pb-3 text-left font-medium text-[var(--color-ink-dim)]">Salle</th>
                      <th className="pb-3 text-right font-medium text-[var(--color-ink-dim)]">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[var(--color-border-soft)]">
                    {sorted.map((s) => (
                      <tr key={s.id} className="group hover:bg-[var(--color-surface-2)]">
                        <td className="py-3 font-medium text-[var(--color-ink)]">{s.jour_semaine}</td>
                        <td className="py-3 font-[var(--font-mono)] text-xs text-[var(--color-ink-dim)]">
                          {hhmm(s.heure_debut)} — {hhmm(s.heure_fin)}
                        </td>
                        <td className="py-3 text-[var(--color-ink-dim)]">{s.cours?.nom ?? '—'}</td>
                        <td className="py-3 text-[var(--color-ink-dim)]">
                          {s.cours?.enseignant ? `${s.cours.enseignant.prenom} ${s.cours.enseignant.nom}` : '—'}
                        </td>
                        <td className="py-3 text-[var(--color-ink-dim)]">
                          {s.classe ? `${s.classe.niveau} — ${s.classe.nom}` : '—'}
                        </td>
                        <td className="py-3 text-[var(--color-ink-dim)]">{s.salle?.nom ?? '—'}</td>
                        <td className="py-3 text-right">
                          <div className="flex items-center justify-end gap-1 opacity-0 transition-all group-hover:opacity-100">
                            {canWrite && (
                              <button
                                onClick={() => handleEdit(s)}
                                className="rounded-[var(--radius-sm)] p-1.5 text-[var(--color-ink-dim)] transition-colors hover:bg-[var(--color-surface-3)] hover:text-[var(--color-ink)]"
                                aria-label="Modifier"
                              >
                                <Pencil size={14} strokeWidth={1.75} />
                              </button>
                            )}
                            {canDelete && (
                              <button
                                onClick={() => setDeleting(s)}
                                className="rounded-[var(--radius-sm)] p-1.5 text-[var(--color-ink-dim)] transition-colors hover:bg-[var(--color-danger-wash)] hover:text-[var(--color-danger)]"
                                aria-label="Supprimer"
                              >
                                <Trash2 size={14} strokeWidth={1.75} />
                              </button>
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
      </div>

      <SeanceFormDrawer
        open={drawerOpen}
        onClose={() => { setDrawerOpen(false); setEditing(null) }}
        onSubmit={handleFormSubmit}
        initial={editing ? {
          id_cours: editing.id_cours,
          id_classe: editing.id_classe,
          id_annee_scolaire: editing.id_annee_scolaire,
          id_salle: editing.id_salle,
          jour_semaine: editing.jour_semaine,
          heure_debut: editing.heure_debut,
          heure_fin: editing.heure_fin,
        } : null}
      />

      <ConfirmDialog
        open={!!deleting}
        onClose={() => setDeleting(null)}
        onConfirm={() => {
          if (deleting) {
            scheduleDeleteWithUndo(() => deleteMut.mutate(deleting.id), 'Séance supprimée.')
          }
        }}
        title="Supprimer cette séance ?"
        description="Cette action est irréversible."
        confirmLabel="Supprimer"
        variant="danger"
      />
    </div>
  )
}
