import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuth } from '@/auth/useAuth'
import { fetchAnneesScolaires } from '@/features/annees_scolaires/api'
import { fetchClasses, fetchClasseDetail, fetchTrimestres, fetchExistingNotes, createNote, updateNote, deleteNote } from './api'
import type { Note, NoteCreatePayload } from './api'
import { Link } from 'react-router-dom'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Select } from '@/components/ui/Select'
import { TableSkeleton } from '@/components/ui/TableSkeleton'
import { Table, TableBody, TableCell, TableContainer, TableHead, TableHeader, TableRow } from '@/components/ui/Table'
import { EmptyState } from '@/components/ui/EmptyState'
import { Avatar } from '@/components/ui/Avatar'
import { extractErrorMessage } from '@/lib/api'
import { toast } from '@/components/ui/toast'
import { Save } from 'lucide-react'
import { baremeNiveau, noteColor, appreciation } from '@/lib/bareme'

const EMPTY_ARRAY: [] = []

interface StudentRow {
  matricule: string
  nom: string
  prenom: string
  existingNote: Note | null
  localValue: string
}

export default function NoteListPage() {
  const { user } = useAuth()
  const canWrite = user?.role === 'admin' || user?.role === 'directeur'
  const queryClient = useQueryClient()

  const [classeId, setClasseId] = useState<number | null>(null)
  const [trimestreId, setTrimestreId] = useState<number | null>(null)
  const [coursId, setCoursId] = useState<number | null>(null)
  const [rows, setRows] = useState<StudentRow[]>([])
  const [saveError, setSaveError] = useState<string | null>(null)

  const { data: classes = EMPTY_ARRAY } = useQuery({ queryKey: ['classes'], queryFn: fetchClasses })
  const { data: annees = EMPTY_ARRAY } = useQuery({ queryKey: ['annees-scolaires'], queryFn: fetchAnneesScolaires })

  const [filterAnnee, setFilterAnnee] = useState('')
  const filterInit = useRef(false)
  useEffect(() => {
    if (!filterInit.current && annees.length > 0) {
      const active = annees.find((a) => a.active)
      if (active) setFilterAnnee(active.id.toString())
      filterInit.current = true
    }
  }, [annees])

  const { data: trimestres = EMPTY_ARRAY } = useQuery({
    queryKey: ['trimestres', filterAnnee],
    queryFn: () => fetchTrimestres(filterAnnee ? Number(filterAnnee) : undefined),
  })

  const { data: classeDetail, isLoading: loadingClasse } = useQuery({
    queryKey: ['classe-detail', classeId],
    queryFn: () => fetchClasseDetail(classeId!),
    enabled: classeId != null,
  })

  function getNiveauNumber(niveau: string): number {
    return parseInt(niveau, 10) || 0
  }

  const filteredTrimestres = useMemo(() => {
    const num = classeDetail ? getNiveauNumber(classeDetail.niveau) : 0
    if (num === 0) return trimestres
    const wantedType = num >= 1 && num <= 6 ? 'COMPOSITION' : 'TRIMESTRE'
    return trimestres.filter((t) => t.type === wantedType)
  }, [trimestres, classeDetail])

  useEffect(() => {
    if (trimestreId != null && filteredTrimestres.length > 0 && !filteredTrimestres.some((t) => t.id === trimestreId)) {
      setTrimestreId(null)
    }
  }, [filteredTrimestres, trimestreId])

  const bareme = useMemo(() => {
    // Classe non encore chargée : on masque la saisie plutôt que de deviner
    // un barème (EF1 /10, EF2 /20).
    return classeDetail ? baremeNiveau(classeDetail.niveau) : null
  }, [classeDetail])

  const selectedCours = useMemo(() => {
    if (!classeDetail || coursId == null) return null
    return classeDetail.cours.find((c) => c.id === coursId) ?? null
  }, [classeDetail, coursId])

  const matriculeEnseignant = selectedCours?.enseignant?.matricule ?? ''

  const { data: existingNotes = EMPTY_ARRAY, isLoading: loadingNotes, isError: erreurNotes } = useQuery({
    queryKey: ['existing-notes', classeId, coursId, trimestreId],
    queryFn: () => fetchExistingNotes({ id_classe: classeId!, id_cours: coursId!, id_trimestre: trimestreId! }),
    enabled: classeId != null && coursId != null && trimestreId != null,
  })

  const notesByEleve = useMemo(() => {
    const map = new Map<string, Note>()
    for (const n of existingNotes) {
      map.set(n.matricule_eleve, n)
    }
    return map
  }, [existingNotes])

  useEffect(() => {
    if (!classeDetail) return
    const sorted = [...classeDetail.eleves].sort((a, b) => a.nom.localeCompare(b.nom))
    setRows(
      sorted.map((e) => ({
        matricule: e.matricule,
        nom: e.nom,
        prenom: e.prenom,
        existingNote: notesByEleve.get(e.matricule) ?? null,
        localValue: notesByEleve.get(e.matricule)?.note?.toString() ?? '',
      })),
    )
  }, [classeDetail, notesByEleve])

  const updateLocal = useCallback((matricule: string, value: string) => {
    if (value !== '' && value.includes('-')) return
    if (bareme == null) return
    if (value !== '' && (isNaN(Number(value)) || Number(value) > bareme)) return
    setRows((prev) =>
      prev.map((r) => (r.matricule === matricule ? { ...r, localValue: value } : r)),
    )
  }, [bareme])

  const hasChanges = useMemo(() => {
    return rows.some((r) => {
      const existing = r.existingNote?.note
      const local = r.localValue === '' ? null : parseFloat(r.localValue)
      return existing !== local
    })
  }, [rows])

  const mutation = useMutation({
    mutationFn: async () => {
      if (!classeId || !coursId || trimestreId == null) return
      if (bareme == null) return
      if (!matriculeEnseignant) {
        throw new Error("Ce cours n'a pas d'enseignant assigné : impossible d'enregistrer les notes.")
      }

      const payload: NoteCreatePayload = {
        note: 0,
        matricule_eleve: '',
        id_cours: coursId,
        id_classe: classeId,
        matricule_enseignant: matriculeEnseignant,
        id_trimestre: trimestreId,
      }

      for (const row of rows) {
        if (row.localValue === '') {
          if (row.existingNote) {
            await deleteNote(row.existingNote.id)
          }
          continue
        }
        const val = parseFloat(row.localValue)
        if (isNaN(val) || val < 0 || val > bareme) continue

        const notePayload = { ...payload, note: val, matricule_eleve: row.matricule }

        if (row.existingNote) {
          await updateNote(row.existingNote.id, notePayload)
        } else {
          await createNote(notePayload)
        }
      }
    },
    onSuccess: () => {
      setSaveError(null)
      toast('Notes enregistrées.')
      queryClient.invalidateQueries({ queryKey: ['existing-notes', classeId, coursId, trimestreId] })
    },
    onError: (err: Error) => {
      setSaveError(extractErrorMessage(err, "Erreur lors de l'enregistrement."))
    },
  })

  const resetSelections = () => {
    setCoursId(null)
    setRows([])
  }

  const stats = useMemo(() => {
    const filled = rows.filter((r) => r.localValue !== '').length
    const total = rows.length
    return { filled, total }
  }, [rows])

  const ready = classeId != null && trimestreId != null && coursId != null

  return (
    <div className="w-full">
      <div className="flex flex-col gap-5">
        <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
          <div>
            <h2 className="text-2xl font-semibold tracking-tight text-[var(--color-ink)]">
              Saisie des notes
            </h2>
            <p className="mt-1 text-sm text-[var(--color-ink-dim)]">
              Sélectionnez une classe, une période et une matière pour saisir les notes
            </p>
          </div>
          {canWrite && ready && rows.length > 0 && (
            <Button
              variant="primary"
              onClick={() => mutation.mutate()}
              disabled={!hasChanges || mutation.isPending || !matriculeEnseignant}
              isLoading={mutation.isPending}
            >
              <Save strokeWidth={1.75} className="size-4" />
              Enregistrer
            </Button>
          )}
        </div>

        <div className="flex flex-wrap gap-4">
          <div className="w-48">
            <Select
              label="Année scolaire"
              value={filterAnnee}
              onChange={(e) => setFilterAnnee(e.target.value)}
            >
              <option value="">Toutes les années</option>
              {annees.map((a) => (
                <option key={a.id} value={a.id}>{a.libelle}</option>
              ))}
            </Select>
          </div>

          <div className="w-48">
            <Select
              label="Classe"
              value={classeId ?? ''}
              onChange={(e) => {
                const v = e.target.value ? Number(e.target.value) : null
                setClasseId(v)
                resetSelections()
              }}
            >
              <option value="">Toutes les classes</option>
              {classes.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.niveau} — {c.nom}
                </option>
              ))}
            </Select>
          </div>

          <div className="w-48">
            <Select
              label="Période"
              value={trimestreId ?? ''}
              onChange={(e) => setTrimestreId(e.target.value ? Number(e.target.value) : null)}
              disabled={!classeDetail}
            >
              <option value="">
                {classeDetail ? "Toutes les périodes" : "D'abord une classe"}
              </option>
              {filteredTrimestres.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.nom}
                </option>
              ))}
            </Select>
          </div>

          <div className="w-48">
            <Select
              label="Matière"
              value={coursId ?? ''}
              onChange={(e) => setCoursId(e.target.value ? Number(e.target.value) : null)}
              disabled={!classeDetail}
            >
              <option value="">
                {classeDetail ? "Toutes les matières" : "D'abord une classe"}
              </option>
              {classeDetail?.cours.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.nom}
                </option>
              ))}
            </Select>
          </div>
        </div>

        {!ready ? (
          <div className="py-16">
            {classeId != null && filteredTrimestres.length === 0 ? (
              <EmptyState
                title="Aucune période pour cette année"
                message="Aucune composition ni aucun trimestre n'est défini pour l'année scolaire sélectionnée. Créez les périodes de cette année avant de saisir les notes."
              />
            ) : (
              <EmptyState message="Sélectionnez une classe, une période et une matière pour commencer la saisie." />
            )}
          </div>
        ) : loadingClasse || loadingNotes ? (
          <TableSkeleton rows={8} />
        ) : erreurNotes ? (
          <div className="py-16">
            <EmptyState message="Impossible de charger les notes de cette matière." />
          </div>
        ) : rows.length === 0 ? (
          <div className="py-16">
            <EmptyState message="Aucun élève dans cette classe." />
          </div>
        ) : (
          <>
            {selectedCours?.enseignant ? (
              <p className="text-sm text-[var(--color-ink-dim)]">
                Enseignant :{' '}
                <span className="font-medium text-[var(--color-ink)]">
                  {selectedCours.enseignant.prenom} {selectedCours.enseignant.nom}
                </span>
              </p>
            ) : (
              <p className="text-sm text-[var(--color-warning)]">
                Aucun enseignant assigné à ce cours : l'enregistrement des notes est désactivé.
              </p>
            )}

            <TableContainer>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Élève</TableHead>
                    <TableHead className="text-center">{bareme != null ? `Note /${bareme}` : 'Note'}</TableHead>
                    <TableHead>Appréciation</TableHead>
                    <TableHead className="text-center">Statut</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {rows.map((row) => {
                    const parsed = row.localValue === '' ? null : parseFloat(row.localValue)
                    const isValid = bareme != null && parsed != null && !isNaN(parsed) && parsed >= 0 && parsed <= bareme
                    const isModified = row.existingNote && parsed !== row.existingNote.note
                    const isNew = !row.existingNote && parsed != null && !isNaN(parsed)

                    return (
                      <TableRow key={row.matricule}>
                        <TableCell>
                          <Link to={`/app/eleves/${row.matricule}`} className="flex items-center gap-3 group">
                            <Avatar nom={row.nom} prenom={row.prenom} size="sm" />
                            <span className="font-medium text-[var(--color-ink)] group-hover:text-[var(--color-brand-bright)]">
                              {row.prenom} {row.nom}
                            </span>
                          </Link>
                        </TableCell>
                        <TableCell className="text-center">
                          <input
                            type="number"
                            min={0}
                            max={bareme ?? undefined}
                            step={bareme === 10 ? 0.25 : 0.5}
                            value={row.localValue}
                            onChange={(e) => updateLocal(row.matricule, e.target.value)}
                            onKeyDown={(e) => {
                              if (e.ctrlKey || e.metaKey) return
                              const allowed = ['Backspace', 'Delete', 'Tab', 'Escape', 'Enter', 'ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', 'Home', 'End']
                              if (allowed.includes(e.key)) return
                              if (!/^[\d.]$/.test(e.key)) e.preventDefault()
                            }}
                            onPaste={(e) => {
                              const data = e.clipboardData.getData('text')
                              if (!/^[\d.]+$/.test(data)) e.preventDefault()
                            }}
                            disabled={!canWrite}
                            aria-label={`Note de ${row.prenom} ${row.nom}`}
                            className="w-20 rounded-[var(--radius-sm)] border border-[var(--color-border)] bg-[var(--color-surface-2)] px-2 py-1.5 text-center text-sm text-[var(--color-ink)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-halo)] disabled:opacity-50"
                          />
                        </TableCell>
                        <TableCell>
                          {isValid && bareme != null ? (
                            <Badge tone={noteColor(parsed!, bareme)}>
                              {appreciation(parsed!, bareme)}
                            </Badge>
                          ) : (
                            <span className="text-[var(--color-ink-faint)]">—</span>
                          )}
                        </TableCell>
                        <TableCell className="text-center">
                          {isModified ? (
                            <span className="text-xs font-medium text-[var(--color-warning)]">Modifié</span>
                          ) : row.existingNote ? (
                            <span className="text-xs text-[var(--color-success)]">Enregistré</span>
                          ) : isNew ? (
                            <span className="text-xs text-[var(--color-info)]">Nouveau</span>
                          ) : (
                            <span className="text-[var(--color-ink-faint)]">—</span>
                          )}
                        </TableCell>
                      </TableRow>
                    )
                  })}
                </TableBody>
              </Table>
            </TableContainer>

            <p className="text-sm text-[var(--color-ink-dim)]">
              {stats.filled}/{stats.total} notes saisies
            </p>

            {saveError && (
              <p className="rounded-[var(--radius-sm)] bg-[var(--color-danger)]/10 px-4 py-2 text-sm text-[var(--color-danger)]">
                {saveError}
              </p>
            )}
          </>
        )}
      </div>
    </div>
  )
}
