import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchAnneesScolaires } from '@/features/annees_scolaires/api'
import { fetchClasses, fetchClasseDetail, fetchTrimestres, fetchExistingNotes, createNote, patchNote, deleteNote, saveNotesBulk, fetchSaisieAutorisee, fetchRegistreNotes } from './api'
import type { Note, NoteBulkItem } from './api'
import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/Button'
import { PageHeader } from '@/components/ui/PageHeader'
import { Select } from '@/components/ui/Select'
import { PageToolbar, ToolbarSearch, ToolbarSpacer } from '@/components/ui/PageToolbar'
import { Switch } from '@/components/ui/Switch'
import { TableSkeleton } from '@/components/ui/TableSkeleton'
import { Table, TableBody, TableCell, TableContainer, TableHead, TableHeader, TableRow } from '@/components/ui/Table'
import { EmptyState } from '@/components/ui/EmptyState'
import { Avatar } from '@/components/ui/Avatar'
import { extractErrorMessage } from '@/lib/api'
import { toast } from '@/components/ui/toast'
import { Save, FileText, Lock } from 'lucide-react'
import { baremeNiveau } from '@/lib/bareme'
import { estNiveauJardin } from '@/lib/niveaux'
import { RegistreDocument } from './RegistreDocument'
import { DocumentPrintModal } from './DocumentPrintModal'

const EMPTY_ARRAY: [] = []

/** Type D — .note-input : mono, 34px, focus action-ring, .invalid en erreur. */
function NoteInput({
  value,
  onChange,
  disabled,
  isInvalid,
  ariaLabel,
  cellKey,
  registerRef,
  onCommit,
  onBlur,
  max,
}: {
  value: string
  onChange: (value: string) => void
  disabled: boolean
  isInvalid: boolean
  ariaLabel: string
  cellKey: string
  registerRef: (key: string, el: HTMLInputElement | null) => void
  onCommit: (key: string, dir: 'next' | 'prev', column: 'next' | 'same') => void
  onBlur?: () => void
  max?: number
}) {
  return (
    <input
      type="text"
      inputMode="decimal"
      autoComplete="off"
      spellCheck={false}
      value={value}
      ref={(el) => registerRef(cellKey, el)}
      onChange={(e) => {
        let raw = e.target.value.replace(/,/g, '.').replace(/[^0-9.]/g, '')
        const firstDot = raw.indexOf('.')
        if (firstDot !== -1) raw = raw.slice(0, firstDot + 1) + raw.slice(firstDot + 1).replace(/\./g, '')
        if (max != null && raw !== '' && !isNaN(Number(raw)) && Number(raw) > max) return
        onChange(raw)
      }}
      onFocus={(e) => e.target.select()}
      onBlur={onBlur}
      onKeyDown={(e) => {
        if (e.ctrlKey || e.metaKey) return
        if (e.key === 'Tab') {
          e.preventDefault()
          onCommit(cellKey, e.shiftKey ? 'prev' : 'next', 'same')
        } else if (e.key === 'Enter') {
          e.preventDefault()
          onCommit(cellKey, e.shiftKey ? 'prev' : 'next', 'next')
        }
      }}
      disabled={disabled}
      aria-label={ariaLabel}
      data-cell={cellKey}
      className={`h-[34px] w-20 rounded-[var(--radius-sm)] border bg-[var(--surface-2)] text-center font-[var(--font-mono)] text-[13px] font-medium text-[var(--ink)] outline-none transition-[border-color,background] duration-100 focus:border-[var(--action)] focus:bg-[var(--surface)] focus:shadow-[0_0_0_2px_var(--action-ring)] disabled:opacity-50 ${
        isInvalid ? 'border-[var(--danger)] text-[var(--danger)]' : 'border-transparent'
      }`}
    />
  )
}

interface StudentRow {
  matricule: string
  nom: string
  prenom: string
  existingNote: Note | null
  localValue: string
  localClasse: string
}

export default function NoteListPage() {
  const queryClient = useQueryClient()

  const [classeId, setClasseId] = useState<number | null>(null)
  const [trimestreId, setTrimestreId] = useState<number | null>(null)
  const [coursId, setCoursId] = useState<number | null>(null)
  const [rows, setRows] = useState<StudentRow[]>([])
  const [saveError, setSaveError] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const [afficherEcartsType, setAfficherEcartsType] = useState(false)
  const [registreOuvert, setRegistreOuvert] = useState(false)
  const inputRefs = useRef(new Map<string, HTMLInputElement>())

  const registerRef = useCallback((key: string, el: HTMLInputElement | null) => {
    if (el) inputRefs.current.set(key, el)
    else inputRefs.current.delete(key)
  }, [])

  const commitNav = useCallback((key: string, dir: 'next' | 'prev', column: 'next' | 'same') => {
    const match = /^([a-z]+):(\d+)$/.exec(key)
    if (!match) return
    let prefix = match[1]
    let index = Number(match[2])
    // Tab → cellule suivante dans la même colonne ; Entrée → ligne suivante.
    if (column === 'same') {
      index += dir === 'next' ? 1 : -1
    } else {
      // Ligne suivante → on revient à la 1re colonne éditable de la ligne cible.
      index += dir === 'next' ? 1 : -1
      if (dir === 'next') prefix = prefix === 'classe' ? 'comp' : prefix
      else if (index >= 0 && prefix === 'comp') prefix = 'classe'
    }
    const el = inputRefs.current.get(`${prefix}:${index}`)
    if (el) {
      el.focus()
      el.select()
    }
  }, [])

  const { data: classes = EMPTY_ARRAY } = useQuery({ queryKey: ['classes'], queryFn: fetchClasses })
  const { data: annees = EMPTY_ARRAY } = useQuery({
    queryKey: ['anneesScolaires'],
    queryFn: fetchAnneesScolaires,
  })

  const [filterAnnee, setFilterAnnee] = useState('')
  const activeAnnee = annees.find((a) => a.active)
  useEffect(() => {
    // Année par défaut : l'année active — mais l'utilisateur reste libre de
    // consulter des années antérieures (archivées) via le sélecteur.
    if (activeAnnee && filterAnnee === '') {
      setFilterAnnee(String(activeAnnee.id))
    }
  }, [activeAnnee, filterAnnee])

  const anneeLibelle = annees.find((a) => String(a.id) === filterAnnee)?.libelle ?? null

  const { data: saisieAutorisee } = useQuery({
    queryKey: ['notes-saisie-autorisee', filterAnnee],
    queryFn: () => fetchSaisieAutorisee(filterAnnee ? Number(filterAnnee) : undefined),
    enabled: !!filterAnnee,
  })

  // Saisie réellement autorisée : trimestre non verrouillé ET année non clôturée.
  const trimestreSaisie = useMemo(() => {
    if (trimestreId == null || !saisieAutorisee) return null
    return saisieAutorisee.trimestres.find((t) => t.id === trimestreId) ?? null
  }, [trimestreId, saisieAutorisee])
  const canWrite =
    !!saisieAutorisee &&
    !saisieAutorisee.annee_cloturee &&
    saisieAutorisee.peut_saisir &&
    (trimestreId == null || !!trimestreSaisie?.peut_saisir)

  const { data: trimestres = EMPTY_ARRAY } = useQuery({
    queryKey: ['trimestres', filterAnnee],
    queryFn: () => fetchTrimestres(filterAnnee ? Number(filterAnnee) : undefined),
    enabled: !!filterAnnee,
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
    // 1ère-5ème : compositions uniquement ; 7ème-9ème+lycée : trimestres.
    // 6ème (classe spéciale) : trimestres + compositions intermédiaires.
    const wantedType = num >= 1 && num <= 5 ? 'COMPOSITION' : 'TRIMESTRE'
    return num === 6 ? trimestres : trimestres.filter((t) => t.type === wantedType)
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

  const estJardin = classeDetail ? estNiveauJardin(classeDetail.niveau) : false

  const selectedCours = useMemo(() => {
    if (!classeDetail || coursId == null) return null
    return classeDetail.cours.find((c) => c.id === coursId) ?? null
  }, [classeDetail, coursId])

  const coeffCours = useMemo(() => {
    if (!selectedCours || !classeDetail) return 1
    return (
      selectedCours.coefficients?.find((c) => c.id_classe === classeDetail.id)?.coefficient ?? 1
    )
  }, [selectedCours, classeDetail])

  const matriculeEnseignant = selectedCours?.enseignant?.matricule ?? ''

  const trimestreNom = useMemo(() => {
    if (trimestreId == null) return null
    return filteredTrimestres.find((t) => t.id === trimestreId)?.nom ?? null
  }, [trimestreId, filteredTrimestres])

  const { data: existingNotes = EMPTY_ARRAY, isLoading: loadingNotes, isError: erreurNotes } = useQuery({
    queryKey: ['existing-notes', classeId, coursId, trimestreId, filterAnnee],
    queryFn: () => fetchExistingNotes({
      id_classe: classeId!,
      id_cours: coursId!,
      id_trimestre: trimestreId!,
      id_annee_scolaire: filterAnnee ? Number(filterAnnee) : undefined,
    }),
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
        localClasse: notesByEleve.get(e.matricule)?.note_classe?.toString() ?? '',
      })),
    )
  }, [classeDetail, notesByEleve])

  const updateLocal = useCallback((matricule: string, value: string) => {
    if (value !== '' && value.includes('-')) return
    if (value !== '' && isNaN(Number(value))) return
    if (bareme != null && value !== '' && !isNaN(Number(value)) && Number(value) > bareme) return
    setRows((prev) =>
      prev.map((r) => (r.matricule === matricule ? { ...r, localValue: value } : r)),
    )
  }, [bareme])

  const updateLocalClasse = useCallback((matricule: string, value: string) => {
    if (value !== '' && value.includes('-')) return
    if (value !== '' && isNaN(Number(value))) return
    if (bareme != null && value !== '' && !isNaN(Number(value)) && Number(value) > bareme) return
    setRows((prev) =>
      prev.map((r) => (r.matricule === matricule ? { ...r, localClasse: value } : r)),
    )
  }, [bareme])

  const hasChanges = useMemo(() => {
    return rows.some((r) => {
      const existingNote = r.existingNote?.note
      const localNote = r.localValue === '' ? null : parseFloat(r.localValue)
      const existingClasse = r.existingNote?.note_classe ?? null
      const localClasse = r.localClasse === '' ? null : parseFloat(r.localClasse)
      return existingNote !== localNote || existingClasse !== localClasse
    })
  }, [rows])

  const autosaveEnCours = useRef<Promise<unknown> | null>(null)

  const mutation = useMutation({
    mutationFn: async () => {
      if (!classeId || !coursId || trimestreId == null) return
      if (bareme == null) return
      if (!matriculeEnseignant) {
        throw new Error("Ce cours n'a pas d'enseignant assigné : impossible d'enregistrer les notes.")
      }

      // Termine l'auto-enregistrement (blur) éventuellement en vol, pour éviter
      // une double création concurrente sur la même note.
      if (autosaveEnCours.current) await autosaveEnCours.current.catch(() => {})

      const base = {
        matricule_eleve: '',
        id_cours: coursId,
        id_classe: classeId,
        matricule_enseignant: matriculeEnseignant,
        id_trimestre: trimestreId,
      }

      const items: NoteBulkItem[] = []
      const aSupprimer: number[] = []

      for (const row of rows) {
        const val = row.localValue === '' ? null : parseFloat(row.localValue)
        const valClasse = row.localClasse === '' ? null : parseFloat(row.localClasse)

        if (val == null && valClasse == null) {
          if (row.existingNote) aSupprimer.push(row.existingNote.id)
          continue
        }
        if (val != null && (isNaN(val) || val < 0 || val > bareme)) continue
        if (valClasse != null && (isNaN(valClasse) || valClasse < 0 || valClasse > bareme)) continue

        items.push({
          ...base,
          id: row.existingNote?.id,
          note: val,
          note_classe: valClasse ?? null,
          matricule_eleve: row.matricule,
        })
      }

      if (items.length > 0) await saveNotesBulk(items)
      for (const id of aSupprimer) await deleteNote(id)
    },
    onSuccess: () => {
      setSaveError(null)
      toast('Notes enregistrées.')
      queryClient.invalidateQueries({ queryKey: ['existing-notes', classeId, coursId, trimestreId, filterAnnee] })
    },
    onError: (err: Error) => {
      setSaveError(extractErrorMessage(err, "Erreur lors de l'enregistrement."))
    },
  })

  const resetSelections = () => {
    setCoursId(null)
    setRows([])
  }

  const filteredRows = useMemo(() => {
    const q = search.trim().toLowerCase()
    if (!q) return rows
    return rows.filter((r) => `${r.prenom} ${r.nom}`.toLowerCase().includes(q))
  }, [rows, search])

  const autosaveMutation = useMutation({
    mutationFn: async ({
      matricule,
      localValue,
      localClasse,
    }: {
      matricule: string
      localValue: string
      localClasse: string
    }): Promise<'unchanged' | 'deleted' | Note | null> => {
      if (!classeId || !coursId || trimestreId == null || bareme == null) return 'unchanged'
      if (!matriculeEnseignant) return 'unchanged'
      const row = rows.find((r) => r.matricule === matricule)
      if (!row) return 'unchanged'

      const val = localValue === '' ? null : parseFloat(localValue)
      const valClasse = localClasse === '' ? null : parseFloat(localClasse)
      const invalid = val != null && (isNaN(val) || val < 0 || val > bareme)
      const invalidClasse = valClasse != null && (isNaN(valClasse) || valClasse < 0 || valClasse > bareme)
      if (invalid || invalidClasse) return 'unchanged'

      const unchanged =
        row.existingNote != null &&
        val === row.existingNote.note &&
        valClasse === (row.existingNote.note_classe ?? null)
      if (unchanged) return 'unchanged'

      const base = {
        matricule_eleve: matricule,
        id_cours: coursId,
        id_classe: classeId,
        matricule_enseignant: matriculeEnseignant,
        id_trimestre: trimestreId,
      }

      if (val == null && valClasse == null) {
        if (row.existingNote) {
          await deleteNote(row.existingNote.id)
          return 'deleted'
        }
        return 'unchanged'
      }

      if (row.existingNote) {
        return await patchNote(row.existingNote.id, {
          ...base,
          note: val,
          note_classe: valClasse ?? null,
        })
      }
      return await createNote({
        ...base,
        note: val,
        note_classe: valClasse ?? undefined,
      })
    },
    onSuccess: (result, { matricule }) => {
      if (result === 'unchanged') return
      if (result === 'deleted') {
        setRows((prev) =>
          prev.map((r) => (r.matricule === matricule ? { ...r, existingNote: null } : r)),
        )
      } else if (result != null) {
        setRows((prev) =>
          prev.map((r) => (r.matricule === matricule ? { ...r, existingNote: result } : r)),
        )
      }
    },
    onError: (err: Error) => {
      toast(extractErrorMessage(err, "Échec de l'enregistrement automatique."), 'error')
    },
  })

  const declencherAutosave = useCallback(
    (row: { matricule: string; localValue: string; localClasse: string }) => {
      const promesse = autosaveMutation.mutateAsync({
        matricule: row.matricule,
        localValue: row.localValue,
        localClasse: row.localClasse,
      })
      autosaveEnCours.current = promesse
      promesse
        .catch(() => {})
        .finally(() => {
          if (autosaveEnCours.current === promesse) autosaveEnCours.current = null
        })
    },
    [autosaveMutation],
  )

  const stats = useMemo(() => {
    const filled = rows.filter((r) => r.localValue !== '').length
    const total = rows.length
    const manquantes = rows.filter((r) => r.localValue === '' && r.localClasse === '').length
    const valeurs = rows
      .map((r) => {
        if (bareme == null) return null
        const c = r.localValue === '' ? null : parseFloat(r.localValue)
        const cl = r.localClasse === '' ? null : parseFloat(r.localClasse)
        if (c == null || isNaN(c)) return null
        const eff = c * 0.6 + (cl != null && !isNaN(cl) ? cl : c) * 0.4
        return eff >= 0 && eff <= bareme ? eff : null
      })
      .filter((v): v is number => v != null)
    const comptesComp = rows
      .map((r) => {
        if (bareme == null) return null
        return r.localValue === '' ? null : parseFloat(r.localValue)
      })
      .filter((v): v is number => v != null && !isNaN(v) && bareme != null && v >= 0 && v <= bareme)
    const moyenneComp =
      comptesComp.length > 0 ? comptesComp.reduce((a, b) => a + b, 0) / comptesComp.length : 0
    return {
      filled,
      total,
      manquantes,
      moyenne: valeurs.length > 0 ? valeurs.reduce((a, b) => a + b, 0) / valeurs.length : null,
      ecartTypeComp:
        comptesComp.length > 0
          ? Math.sqrt(
              comptesComp.reduce((acc, v) => acc + (v - moyenneComp) ** 2, 0) / comptesComp.length,
            )
          : null,
    }
  }, [rows, bareme])

  const ready = classeId != null && trimestreId != null && coursId != null

  const headerSubtitle = useMemo(() => {
    if (!ready || !classeDetail || !selectedCours || !trimestreNom) {
      return 'Sélectionnez une classe, une période et une matière pour saisir les notes'
    }
    return `${classeDetail.niveau} ${classeDetail.nom} · ${trimestreNom} · ${anneeLibelle ?? ''} · Coef. ${coeffCours}`
  }, [ready, classeDetail, selectedCours, trimestreNom, anneeLibelle, coeffCours])

  const breadcrumb = useMemo(() => {
    if (!ready || !classeDetail || !selectedCours) {
      return [{ label: 'Notes' }]
    }
    return [
      { label: 'Notes', to: '/app/notes' },
      { label: `${selectedCours.nom} · ${classeDetail.niveau} ${classeDetail.nom}` },
    ]
  }, [ready, classeDetail, selectedCours])

  useEffect(() => {
    if (!ready || estJardin || !canWrite) return
    const onKeyDown = (e: KeyboardEvent) => {
      if (!(e.ctrlKey || e.metaKey)) return
      const k = e.key.toLowerCase()
      if (k === 's') {
        e.preventDefault()
        if (hasChanges && !mutation.isPending) mutation.mutate()
      } else if (k === 'enter') {
        e.preventDefault()
        const active = document.activeElement as HTMLElement | null
        const cellKey = active?.dataset?.cell
        const match = cellKey ? /^([a-z]+):(\d+)$/.exec(cellKey) : null
        if (!match) return
        const row = filteredRows[Number(match[2])]
        if (row)
          autosaveMutation.mutate({
            matricule: row.matricule,
            localValue: row.localValue,
            localClasse: row.localClasse,
          })
      }
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [ready, estJardin, hasChanges, mutation, filteredRows, autosaveMutation, canWrite])

  return (
    <div className="w-full">
      <div className="flex flex-col gap-5">
        <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
          <PageHeader
            title="Saisie des notes"
            breadcrumb={breadcrumb}
            subtitle={
              <p className="mt-1 truncate text-sm text-[var(--ink-dim)]">{headerSubtitle}</p>
            }
          />
          {ready && !estJardin && classeId != null && coursId != null && filterAnnee && (
            <Button
              variant="secondary"
              onClick={() => setRegistreOuvert(true)}
              title="Registre de notes de la matière pour l'année sélectionnée (toutes périodes)"
            >
              <FileText strokeWidth={1.75} className="size-4" />
              Registre de notes
            </Button>
          )}
          {canWrite && ready && rows.length > 0 && !estJardin && (
            <Button
              variant="primary"
              onClick={() => mutation.mutate()}
              disabled={mutation.isPending || !matriculeEnseignant}
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
              label="Année"
              value={filterAnnee}
              onChange={(e) => {
                setFilterAnnee(e.target.value)
                setTrimestreId(null)
                resetSelections()
              }}
              disabled={!annees.length}
            >
              <option value="">— Choisir une année —</option>
              {annees.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.libelle}{a.cloturee ? ' (archivée)' : ''}
                </option>
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
              disabled={!classes.length}
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
              disabled={!classeDetail || !filteredTrimestres.length}
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
              disabled={!classeDetail || !classeDetail.cours.length}
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

        {saisieAutorisee != null && !canWrite && (
          <div className="flex items-start gap-2 rounded-[var(--radius-md)] border border-[var(--action-w)] bg-[var(--action-w)] px-4 py-3 text-sm text-[var(--action)]">
            <Lock className="mt-0.5 size-4 shrink-0" strokeWidth={1.75} />
            <p>
              {saisieAutorisee.annee_cloturee
                ? `${anneeLibelle ?? "Cette année"} est clôturée : consultation en lecture seule — aucune note ne peut être saisie ni modifiée.`
                : trimestreSaisie?.verrouille || (trimestreId != null && !trimestreSaisie?.peut_saisir)
                  ? `La période « ${trimestreNom ?? ''} » est verrouillée : la saisie des notes y est désactivée.`
                  : 'La saisie des notes est actuellement désactivée pour cette période.'}
            </p>
          </div>
        )}

        {estJardin ? (
          <div className="py-16">
            <EmptyState
              title="Évaluation par appréciation"
              message="Les classes du jardin d'enfants (Petite, Moyenne et Grande Section) sont évaluées par appréciation de l'enseignant : aucune note chiffrée n'y est saisie."
            />
          </div>
        ) : !ready ? (
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
            <EmptyState title="Erreur" message="Impossible de charger les notes de cette matière." />
          </div>
        ) : rows.length === 0 ? (
          <div className="py-16">
            <EmptyState message="Aucun élève dans cette classe." />
          </div>
        ) : (
          <>
<PageToolbar>
            <ToolbarSearch
              placeholder="Rechercher un élève…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            <ToolbarSpacer />
            <label className="flex h-[30px] items-center gap-2 pl-1 pr-2 text-[12.5px] text-[var(--ink-dim)]">
              <span className="hidden sm:inline">Écarts-type</span>
              <Switch
                checked={afficherEcartsType}
                onChange={setAfficherEcartsType}
                label=""
                ariaLabel="Afficher les écarts-type"
              />
            </label>
          </PageToolbar>

          {selectedCours?.enseignant ? (
            <p className="text-sm text-[var(--ink-dim)]">
              Enseignant :{' '}
              <span className="font-medium text-[var(--ink)]">
                {selectedCours.enseignant.prenom} {selectedCours.enseignant.nom}
              </span>
            </p>
          ) : (
            <p className="text-sm text-[var(--warning)]">
              Aucun enseignant assigné à ce cours : l'enregistrement des notes est désactivé.
            </p>
          )}

          {filteredRows.length === 0 ? (
            <div className="py-16">
              <EmptyState message="Aucun élève ne correspond à la recherche." />
            </div>
          ) : (
            <TableContainer>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Élève</TableHead>
                    <TableHead className="text-center">{bareme != null ? `Comp. /${bareme}` : 'Comp.'}</TableHead>
                    <TableHead className="text-center">{bareme != null ? `Classe /${bareme}` : 'Classe'}</TableHead>
                    <TableHead className="text-center">Moyenne</TableHead>
                    <TableHead className="text-center">Statut</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredRows.map((row, rowIndex) => {
                    const parsed = row.localValue === '' ? null : parseFloat(row.localValue)
                    const parsedClasse = row.localClasse === '' ? null : parseFloat(row.localClasse)
                    const compInvalid =
                      row.localValue !== '' && (parsed == null || isNaN(parsed) || parsed < 0 || parsed > (bareme ?? Infinity))
                    const classeInvalid =
                      row.localClasse !== '' && (parsedClasse == null || isNaN(parsedClasse) || parsedClasse < 0 || parsedClasse > (bareme ?? Infinity))
                    const effective =
                      bareme != null && parsed != null && !isNaN(parsed)
                        ? parsed * 0.6 + (parsedClasse != null && !isNaN(parsedClasse) ? parsedClasse : parsed) * 0.4
                        : null
                    const isValid = bareme != null && effective != null && effective >= 0 && effective <= bareme
                    const isModified =
                      !!row.existingNote &&
                      (parsed !== row.existingNote.note ||
                        parsedClasse !== (row.existingNote.note_classe ?? null))
                    const isNew = !row.existingNote && parsed != null && !isNaN(parsed)

                    return (
                      <TableRow key={row.matricule}>
                        <TableCell>
                          <Link to={`/app/eleves/${row.matricule}`} className="flex items-center gap-3 group">
                            <Avatar nom={row.nom} prenom={row.prenom} size="sm" />
                            <span className="font-medium text-[var(--ink)] group-hover:text-[var(--action-bright)]">
                              {row.prenom} {row.nom}
                            </span>
                          </Link>
                        </TableCell>
                        <TableCell className="text-center">
                          <NoteInput
                            value={row.localValue}
                            onChange={(v) => updateLocal(row.matricule, v)}
                            disabled={!canWrite || autosaveMutation.isPending}
                            isInvalid={compInvalid}
                            max={bareme ?? undefined}
                            cellKey={`comp:${rowIndex}`}
                            registerRef={registerRef}
                            onCommit={commitNav}
                            onBlur={() =>
                            declencherAutosave({
                              matricule: row.matricule,
                              localValue: row.localValue,
                              localClasse: row.localClasse,
                            })
                          }
                            ariaLabel={`Note de composition de ${row.prenom} ${row.nom}`}
                          />
                        </TableCell>
                        <TableCell className="text-center">
                          <NoteInput
                            value={row.localClasse}
                            onChange={(v) => updateLocalClasse(row.matricule, v)}
                            disabled={!canWrite || autosaveMutation.isPending}
                            isInvalid={classeInvalid}
                            max={bareme ?? undefined}
                            cellKey={`classe:${rowIndex}`}
                            registerRef={registerRef}
                            onCommit={commitNav}
                            onBlur={() =>
                            declencherAutosave({
                              matricule: row.matricule,
                              localValue: row.localValue,
                              localClasse: row.localClasse,
                            })
                          }
                            ariaLabel={`Note de classe de ${row.prenom} ${row.nom}`}
                          />
                        </TableCell>
                        <TableCell className="text-center">
                          {isValid && bareme != null && effective != null ? (
                            <span
                              className={`font-[var(--font-mono)] text-[13px] font-semibold px-[10px] ${
                                effective >= bareme / 2 ? 'text-[var(--success)]' : 'text-[var(--danger)]'
                              }`}
                            >
                              {effective.toFixed(2)} / {bareme}
                            </span>
                          ) : (
                            <span className="px-[10px] font-[var(--font-mono)] text-[13px] italic text-[var(--ink-faint)]">
                              —
                            </span>
                          )}
                        </TableCell>
                        <TableCell className="text-center">
                          {isModified ? (
                            <span className="text-xs font-medium text-[var(--warning)]">Modifié</span>
                          ) : row.existingNote ? (
                            <span className="text-xs text-[var(--success)]">Enregistré</span>
                          ) : isNew ? (
                            <span className="text-xs text-[var(--info)]">Nouveau</span>
                          ) : (
                            <span className="text-[var(--ink-faint)]">—</span>
                          )}
                        </TableCell>
                      </TableRow>
                    )
                  })}
                </TableBody>
              </Table>
            </TableContainer>
          )}

            <div className="flex flex-wrap items-center justify-between gap-2 border-t border-[var(--border-soft)] pt-3">
              <p className="text-sm text-[var(--ink-dim)]">
                Moyenne de classe :{' '}
                {stats.moyenne != null && bareme != null ? (
                  <span className={`font-[var(--font-mono)] text-[13px] font-semibold ${stats.moyenne >= bareme / 2 ? 'text-[var(--success)]' : 'text-[var(--danger)]'}`}>
                    {stats.moyenne.toFixed(2)} / {bareme}
                  </span>
                ) : (
                  <span className="text-[var(--ink-faint)]">—</span>
                )}
              </p>
              <p className="text-sm text-[var(--ink-dim)]">
                {stats.filled}/{stats.total} notes saisies · Manquantes :{' '}
                <span className="font-medium text-[var(--ink)]">{stats.manquantes}</span>
              </p>
            </div>

            {afficherEcartsType && stats.ecartTypeComp != null && (
              <p className="text-sm text-[var(--ink-dim)]">
                Écart-type (composition) :{' '}
                <span className="font-[var(--font-mono)] text-[13px] font-semibold text-[var(--ink)]">
                  {stats.ecartTypeComp.toFixed(2)}
                </span>
              </p>
            )}

            {saveError && (
              <p className="rounded-[var(--radius-sm)] bg-[var(--danger)]/10 px-4 py-2 text-sm text-[var(--danger)]">
                {saveError}
              </p>
            )}
          </>
        )}
      </div>

      {registreOuvert && (
        <RegistreApercuModal
          classeId={classeId}
          coursId={coursId}
          anneeId={filterAnnee ? Number(filterAnnee) : null}
          anneeLabel={anneeLibelle}
          onClose={() => setRegistreOuvert(false)}
        />
      )}
    </div>
  )
}

function RegistreApercuModal({
  classeId,
  coursId,
  anneeId,
  anneeLabel,
  onClose,
}: {
  classeId: number | null
  coursId: number | null
  anneeId: number | null
  anneeLabel: string | null
  onClose: () => void
}) {
  const { data: registre, isLoading, isError } = useQuery({
    queryKey: ['registre-notes', classeId, coursId, anneeId],
    queryFn: () =>
      fetchRegistreNotes({
        classe_id: classeId!,
        cours_id: coursId!,
        annee_id: anneeId!,
      }),
    enabled: classeId != null && coursId != null && anneeId != null,
  })

  return (
    <DocumentPrintModal
      title="Registre de notes"
      onClose={onClose}
    >
      {isLoading ? (
        <div className="py-16 text-center text-sm text-[var(--ink-dim)]">
          Chargement du registre…
        </div>
      ) : isError || !registre ? (
        <div className="py-16 text-center text-sm text-[var(--danger)]">
          Impossible de charger le registre de notes pour cette matière.
        </div>
      ) : (
        <RegistreDocument registre={registre} anneeLabel={anneeLabel ?? undefined} />
      )}
    </DocumentPrintModal>
  )
}
