import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import axios from 'axios'
import {
  ChevronLeft, ChevronRight, CheckCircle, User, Users, School, FileText,
  AlertCircle, Upload, Check, X,
} from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { SearchableSelect } from '@/components/ui/SearchableSelect'
import { fetchClasses } from '@/features/classes/api'
import { fetchAnneesScolaires } from '@/features/annees_scolaires/api'
import { fetchTuteurs } from '@/features/tuteurs/api'
import { creerDossierComplet } from './api'
import { uploadDocument } from '@/features/documents/api'
import { extractErrorMessage } from '@/lib/api'
import { required, email, phone, validateFields, hasErrors, type Errors } from '@/lib/validation'
import type { DossierCompletInput } from './api'

const DOCS_LABELS: Record<string, string> = {
  acte_naissance: 'Acte de naissance',
  carnet_sante: 'Carnet de santé',
}

const STEPS = [
  { id: 1, label: "Identité de l'élève", icon: User },
  { id: 2, label: 'Coordonnées du tuteur', icon: Users },
  { id: 3, label: 'Scolarité', icon: School },
  { id: 4, label: 'Documents', icon: FileText },
  { id: 5, label: 'Confirmation', icon: CheckCircle },
]

interface Props {
  onComplete: () => void
  onCancel: () => void
  canImport?: boolean
}

const emptyForm = {
  nom: '', prenom: '', dateNaissance: '', lieuNaissance: '', sexe: 'M',
  nomPere: '', prenomPere: '', fonctionPere: '', nomMere: '', prenomMere: '', fonctionMere: '',
  tuteurNom: '', tuteurPrenom: '', tuteurEmail: '', tuteurTelephone: '', tuteurAdresse: '', tuteurProfession: '',
  niveauId: '', classeId: '', anneeScolaireId: '',
  acte_naissance: false, carnet_sante: false,
  numero_acte: '', jugement_suppletif: '', date_acte: '', delivre_par: '',
  observation: '',
}

const DOCS_FIELDS = ['acte_naissance', 'carnet_sante'] as const

export default function InscriptionWizard({ onComplete, onCancel, canImport = true }: Props) {
  const [step, setStep] = useState(1)
  const [form, setForm] = useState(emptyForm)
  const [tuteurMode, setTuteurMode] = useState<'create' | 'select'>('create')
  const [tuteurId, setTuteurId] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [submitted, setSubmitted] = useState(false)
  const [codeInscription, setCodeInscription] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [errors, setErrors] = useState<Errors>({})
  const [docFiles, setDocFiles] = useState<Record<string, File | null>>({})
  const [uploadProgress, setUploadProgress] = useState<string | null>(null)

  const { data: classes = [], isLoading: loadingClasses } = useQuery({ queryKey: ['classes'], queryFn: fetchClasses })
  const { data: annees = [] } = useQuery({ queryKey: ['annees-scolaires'], queryFn: fetchAnneesScolaires })
  const { data: tuteurs = [] } = useQuery({ queryKey: ['tuteurs'], queryFn: () => fetchTuteurs() })

  const anneeActive = annees.find((a) => a.active)
  const classesDuNiveau = useMemo(() => {
    if (!form.niveauId) return []
    return classes.filter((c) => c.niveau === form.niveauId)
  }, [classes, form.niveauId])

  const niveaux = useMemo(() => {
    const unique = new Set(classes.map((c) => c.niveau))
    return [...unique].sort()
  }, [classes])

  const set = (k: string, v: string | boolean) => setForm((f) => ({ ...f, [k]: v }))

  const pct = Math.round(((step - 1) / (STEPS.length - 1)) * 100)

  function validateStep(stepNum: number): boolean {
    let errs: Errors = {}
    if (stepNum === 1) {
      errs = validateFields({
        nom: required(form.nom, 'Le nom'),
        prenom: required(form.prenom, 'Le prénom'),
        dateNaissance: required(form.dateNaissance, 'La date de naissance'),
        lieuNaissance: required(form.lieuNaissance, 'Le lieu de naissance'),
      })
    } else if (stepNum === 2) {
      errs = tuteurMode === 'select'
        ? validateFields({ tuteurId: required(tuteurId, 'Le tuteur') })
        : validateFields({
            tuteurNom: required(form.tuteurNom, 'Le nom du tuteur'),
            tuteurPrenom: required(form.tuteurPrenom, 'Le prénom du tuteur'),
            tuteurEmail: required(form.tuteurEmail, "L'e-mail") ?? email(form.tuteurEmail),
            tuteurTelephone: required(form.tuteurTelephone, 'Le téléphone') ?? phone(form.tuteurTelephone),
            tuteurAdresse: required(form.tuteurAdresse, "L'adresse"),
            tuteurProfession: required(form.tuteurProfession, 'La profession'),
          })
    } else if (stepNum === 3) {
      errs = validateFields({
        classeId: required(form.classeId, 'La classe'),
      })
    }
    setErrors(errs)
    return !hasErrors(errs)
  }

  function handleNext() {
    if (validateStep(step)) setStep((s) => s + 1)
  }

  async function handleSubmit() {
    if (!validateStep(1)) return setStep(1)
    if (!validateStep(2)) return setStep(2)
    if (!validateStep(3)) return setStep(3)
    setSubmitting(true)
    setError(null)
    setUploadProgress(null)
    try {
      const input: DossierCompletInput = {
        ...(tuteurMode === 'select' && tuteurId
          ? { tuteur_id: Number(tuteurId) }
          : {
              tuteur: {
                nom: form.tuteurNom,
                prenom: form.tuteurPrenom,
                email: form.tuteurEmail,
                telephone: form.tuteurTelephone,
                adresse: form.tuteurAdresse,
                profession: form.tuteurProfession,
              },
            }),
        eleve: {
          nom: form.nom,
          prenom: form.prenom,
          date_de_naissance: form.dateNaissance,
          lieu_de_naissance: form.lieuNaissance,
          sexe: form.sexe,
          statut: 'actif',
          acte_naissance: form.acte_naissance,
          carnet_sante: form.carnet_sante,
          numero_acte: form.numero_acte.trim() || null,
          jugement_suppletif: form.jugement_suppletif.trim() || null,
          date_acte: form.date_acte || null,
          delivre_par: form.delivre_par.trim() || null,
          nom_pere: form.nomPere.trim() || null,
          prenom_pere: form.prenomPere.trim() || null,
          fonction_pere: form.fonctionPere.trim() || null,
          nom_mere: form.nomMere.trim() || null,
          prenom_mere: form.prenomMere.trim() || null,
          fonction_mere: form.fonctionMere.trim() || null,
        },
        classe_id: form.classeId ? Number(form.classeId) : null,
        id_annee_scolaire: anneeActive?.id ?? Number(form.anneeScolaireId),
        observation: form.observation || null,
      }
      const result = await creerDossierComplet(input)

      const filesToUpload = DOCS_FIELDS.filter((f) => docFiles[f])
      for (const field of filesToUpload) {
        const file = docFiles[field]!
        setUploadProgress(`Upload de ${DOCS_LABELS[field]}…`)
        await uploadDocument(result.matricule_eleve, field, file)
      }

      setUploadProgress(null)
      setCodeInscription(result.code_inscription)
      setSubmitted(true)
      setTimeout(() => onComplete(), 2000)
    } catch (err) {
      // Erreurs métier du backend : 409 (inscription/année clôturée), 400
      // (dossier invalide), 404 (ressource introuvable) — on garde l'utilisateur
      // sur l'étape en cours pour corriger avant de relancer.
      const status = axios.isAxiosError(err) ? err.response?.status : undefined
      if (status === 409) {
        setError(extractErrorMessage(err, "Cette inscription existe déjà pour cette année scolaire."))
      } else if (status === 400) {
        setError(extractErrorMessage(err, 'Le dossier ne peut pas être enregistré : vérifiez les informations saisies.'))
      } else if (status === 404) {
        setError(extractErrorMessage(err, "Une ressource référencée est introuvable (élève, classe, année scolaire ou tuteur)."))
      } else {
        setError(extractErrorMessage(err, "Erreur lors de l'enregistrement."))
      }
      setSubmitting(false)
    }
  }

  return (
    <div className="flex gap-6">
      <div className="w-52 shrink-0">
        <div className="overflow-hidden rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--surface)]">
          <div className="px-4 py-4">
            <p className="text-[13px] font-semibold text-[var(--ink)]">Nouvelle inscription</p>
            <p className="mb-3 text-[11px] text-[var(--ink-faint)]">
              {anneeActive?.libelle ?? 'Année scolaire'}
            </p>
            <div className="mb-4">
              <div className="mb-1 flex justify-between">
                <span className="text-[10px] text-[var(--ink-faint)]">Progression</span>
                <span className="text-[10px] text-[var(--ink-faint)]">{pct}%</span>
              </div>
              <div className="h-1.5 rounded-full bg-[var(--border-soft)]">
                <div
                  className="h-1.5 rounded-full bg-[var(--action)] transition-all duration-500"
                  style={{ width: `${pct}%` }}
                />
              </div>
            </div>
            <div className="space-y-1">
              {STEPS.map((s) => {
                const Icon = s.icon
                const done = s.id < step
                const active = s.id === step
                return (
                  <button
                    key={s.id}
                    onClick={() => done && setStep(s.id)}
                    className="flex w-full items-center gap-3 rounded-[var(--radius-sm)] px-3 py-2.5 text-left transition-all"
                    style={{
                      background: active ? 'var(--surface-2)' : 'transparent',
                      cursor: done ? 'pointer' : 'default',
                    }}
                  >
                    <div
                      className="flex size-6 shrink-0 items-center justify-center rounded-full"
                      style={{
                        background: done ? 'var(--action)' : active ? 'var(--surface)' : 'var(--border-soft)',
                      }}
                    >
                      {done ? (
                        <CheckCircle size={13} className="text-[var(--ink)]" />
                      ) : (
                        <Icon size={13} className={active ? 'text-[var(--ink)]' : 'text-[var(--ink-faint)]'} />
                      )}
                    </div>
                    <span
                      className="text-xs"
                      style={{
                        fontWeight: active ? 600 : 400,
                        color: active ? 'var(--ink)' : done ? 'var(--ink-dim)' : 'var(--ink-faint)',
                      }}
                    >
                      {s.label}
                    </span>
                  </button>
                )
              })}
            </div>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-hidden rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--surface)]">
        <div className="border-b border-[var(--border)] px-6 py-4">
          <p className="text-[15px] font-semibold text-[var(--ink)]">{STEPS[step - 1].label}</p>
          <p className="text-xs text-[var(--ink-dim)]">Étape {step} sur {STEPS.length}</p>
        </div>

        <div className="px-6 py-6">
          {error && (
            <div className="mb-4 flex items-start gap-2 rounded-[var(--radius-sm)] border border-[var(--danger)]/30 bg-[var(--danger-w)] px-3 py-2 text-sm text-[var(--danger)]">
              <AlertCircle size={14} className="mt-0.5 shrink-0" />
              {error}
            </div>
          )}

          {submitted ? (
            <div className="flex flex-col items-center justify-center gap-4 py-12">
              <div className="flex size-16 items-center justify-center rounded-full bg-[var(--success-w)]">
                <CheckCircle size={36} className="text-[var(--success)]" />
              </div>
              <p className="text-lg font-semibold text-[var(--ink)]">Inscription enregistrée.</p>
              {codeInscription && (
                <p className="font-[var(--font-mono)] text-sm text-[var(--mod-res)]">{codeInscription}</p>
              )}
              <p className="text-center text-sm text-[var(--ink-dim)]">
                Le dossier de {form.prenom} {form.nom} a été créé. Redirection...
              </p>
            </div>
          ) : (
            <>
              {step === 1 && (
                <div className="space-y-4">
                  <div className="grid grid-cols-4 gap-4">
                    <Select label="Sexe" value={form.sexe} onChange={(e) => set('sexe', e.target.value)}>
                      <option value="M">Masculin</option>
                      <option value="F">Féminin</option>
                    </Select>
                    <Input
                      label="Nom"
                      placeholder="Traoré"
                      value={form.nom}
                      onChange={(e) => {
                        set('nom', e.target.value)
                        if (errors.nom) setErrors((prev) => ({ ...prev, nom: undefined }))
                      }}
                      required
                      error={errors.nom}
                    />
                    <Input
                      label="Prénom"
                      placeholder="Fatoumata"
                      value={form.prenom}
                      onChange={(e) => {
                        set('prenom', e.target.value)
                        if (errors.prenom) setErrors((prev) => ({ ...prev, prenom: undefined }))
                      }}
                      required
                      error={errors.prenom}
                    />
                    <Input
                      label="Date de naissance"
                      type="date"
                      value={form.dateNaissance}
                      onChange={(e) => {
                        set('dateNaissance', e.target.value)
                        if (errors.dateNaissance) setErrors((prev) => ({ ...prev, dateNaissance: undefined }))
                      }}
                      max={new Date().toISOString().split('T')[0]}
                      required
                      error={errors.dateNaissance}
                    />
                  </div>
                  <Input label="Lieu de naissance" placeholder="Bamako" value={form.lieuNaissance} onChange={(e) => {
                    set('lieuNaissance', e.target.value)
                    if (errors.lieuNaissance) setErrors((prev) => ({ ...prev, lieuNaissance: undefined }))
                  }} required error={errors.lieuNaissance} />
                  <div className="grid grid-cols-3 gap-4">
                    <Input
                      label="Nom du père"
                      placeholder="Diallo"
                      value={form.nomPere}
                      onChange={(e) => set('nomPere', e.target.value)}
                    />
                    <Input
                      label="Prénom du père"
                      placeholder="Modibo"
                      value={form.prenomPere}
                      onChange={(e) => set('prenomPere', e.target.value)}
                    />
                    <Input
                      label="Fonction du père"
                      placeholder="Commerçant"
                      value={form.fonctionPere}
                      onChange={(e) => set('fonctionPere', e.target.value)}
                    />
                  </div>
                  <div className="grid grid-cols-3 gap-4">
                    <Input
                      label="Nom de la mère"
                      placeholder="Coulibaly"
                      value={form.nomMere}
                      onChange={(e) => set('nomMere', e.target.value)}
                    />
                    <Input
                      label="Prénom de la mère"
                      placeholder="Aminata"
                      value={form.prenomMere}
                      onChange={(e) => set('prenomMere', e.target.value)}
                    />
                    <Input
                      label="Fonction de la mère"
                      placeholder="Ménagère"
                      value={form.fonctionMere}
                      onChange={(e) => set('fonctionMere', e.target.value)}
                    />
                  </div>
                  <div className="flex items-start gap-2 rounded-[var(--radius-sm)] border border-[var(--info)]/30 bg-[var(--info-w)] px-3 py-2">
                    <AlertCircle size={14} className="mt-0.5 shrink-0 text-[var(--info)]" />
                    <span className="text-xs text-[var(--info)]">
                      Les champs marqués * sont obligatoires.
                    </span>
                  </div>
                </div>
              )}

              {step === 2 && (
                <div className="space-y-4">
                  <div className="flex items-center gap-3 rounded-[var(--radius-sm)] border border-[var(--border-soft)] bg-[var(--surface-2)] p-3">
                    <button
                      type="button"
                      onClick={() => { setTuteurMode('select'); setTuteurId('') }}
                      className="rounded px-3 py-1.5 text-xs font-medium transition-all"
                      style={{
                        background: tuteurMode === 'select' ? 'var(--action)' : 'var(--surface)',
                        color: tuteurMode === 'select' ? 'var(--ink)' : 'var(--ink-dim)',
                      }}
                    >
                      Tuteur existant
                    </button>
                    <button
                      type="button"
                      onClick={() => setTuteurMode('create')}
                      className="rounded px-3 py-1.5 text-xs font-medium transition-all"
                      style={{
                        background: tuteurMode === 'create' ? 'var(--action)' : 'var(--surface)',
                        color: tuteurMode === 'create' ? 'var(--ink)' : 'var(--ink-dim)',
                      }}
                    >
                      Nouveau tuteur
                    </button>
                  </div>

                  {tuteurMode === 'select' ? (
                    <SearchableSelect
                      label="Choisir un tuteur"
                      value={tuteurId}
                      onChange={(v) => {
                        setTuteurId(v)
                        if (errors.tuteurId) setErrors((prev) => ({ ...prev, tuteurId: undefined }))
                      }}
                      options={tuteurs.map((t) => ({
                        value: String(t.id),
                        label: `${t.prenom} ${t.nom}`.trim(),
                        sublabel: t.telephone,
                      }))}
                      placeholder="Rechercher un tuteur…"
                      emptyMessage="Aucun tuteur trouvé"
                      error={errors.tuteurId}
                    />
                  ) : (
                    <>
                      <div className="grid grid-cols-2 gap-4">
                        <Input
                          label="Nom du tuteur"
                          placeholder="Touré"
                          value={form.tuteurNom}
                          onChange={(e) => {
                            set('tuteurNom', e.target.value)
                            if (errors.tuteurNom) setErrors((prev) => ({ ...prev, tuteurNom: undefined }))
                          }}
                          required
                          error={errors.tuteurNom}
                        />
                        <Input
                          label="Prénom du tuteur"
                          placeholder="Amadou"
                          value={form.tuteurPrenom}
                          onChange={(e) => {
                            set('tuteurPrenom', e.target.value)
                            if (errors.tuteurPrenom) setErrors((prev) => ({ ...prev, tuteurPrenom: undefined }))
                          }}
                          required
                          error={errors.tuteurPrenom}
                        />
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        <Input
                          label="Email"
                          type="email"
                          placeholder="amadou@email.com"
                          value={form.tuteurEmail}
                          onChange={(e) => {
                            set('tuteurEmail', e.target.value)
                            if (errors.tuteurEmail) setErrors((prev) => ({ ...prev, tuteurEmail: undefined }))
                          }}
                          required
                          error={errors.tuteurEmail}
                        />
                        <Input
                          label="Téléphone"
                          placeholder="+223 XX XX XX XX"
                          value={form.tuteurTelephone}
                          onChange={(e) => {
                            set('tuteurTelephone', e.target.value)
                            if (errors.tuteurTelephone) setErrors((prev) => ({ ...prev, tuteurTelephone: undefined }))
                          }}
                          required
                          error={errors.tuteurTelephone}
                        />
                      </div>
                      <Input
                        label="Adresse"
                        placeholder="Badalabougou, Bamako"
                        value={form.tuteurAdresse}
                        onChange={(e) => {
                          set('tuteurAdresse', e.target.value)
                          if (errors.tuteurAdresse) setErrors((prev) => ({ ...prev, tuteurAdresse: undefined }))
                        }}
                        required
                        error={errors.tuteurAdresse}
                      />
                      <Input
                        label="Profession"
                        placeholder="ex. Commerçant"
                        value={form.tuteurProfession}
                        onChange={(e) => {
                          set('tuteurProfession', e.target.value)
                          if (errors.tuteurProfession) setErrors((prev) => ({ ...prev, tuteurProfession: undefined }))
                        }}
                        required
                        error={errors.tuteurProfession}
                      />
                    </>
                  )}
                </div>
              )}

              {step === 3 && (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <Select
                      label="Niveau demandé"
                      value={form.niveauId}
                      onChange={(e) => { set('niveauId', e.target.value); set('classeId', '') }}
                      required
                    >
                      <option value="">— Choisir —</option>
                      {niveaux.map((n) => <option key={n} value={n}>{n}</option>)}
                    </Select>
                    <Select
                      label="Classe attribuée"
                      value={form.classeId}
                      onChange={(e) => set('classeId', e.target.value)}
                      disabled={!form.niveauId}
                    >
                      <option value="">— À attribuer —</option>
                      {classesDuNiveau.map((c) => <option key={c.id} value={c.id}>{c.niveau} — {c.nom}</option>)}
                    </Select>
                  </div>

                  {classesDuNiveau.length > 0 && (
                    <div>
                      <p className="mb-2 text-xs font-semibold text-[var(--ink)]">
                        Classes disponibles {form.niveauId ? `— Niveau ${form.niveauId}` : ''}
                      </p>
                      <div className="grid grid-cols-3 gap-3">
                        {classesDuNiveau.map((c) => (
                          <button
                            key={c.id}
                            type="button"
                            onClick={() => set('classeId', String(c.id))}
                            className="rounded-[var(--radius-sm)] border p-3 text-center transition-all"
                            style={{
                              background: Number(form.classeId) === c.id ? 'var(--info-w)' : 'var(--surface)',
                              borderColor: Number(form.classeId) === c.id ? 'var(--info)' : 'var(--border)',
                            }}
                          >
                            <p className="text-sm font-semibold" style={{ color: Number(form.classeId) === c.id ? 'var(--info)' : 'var(--ink)' }}>
                              {c.niveau} — {c.nom}
                            </p>
                            <p className="text-[11px] text-[var(--ink-faint)]">
                              Salle
                            </p>
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  {!loadingClasses && classesDuNiveau.length === 0 && form.niveauId && (
                    <p className="text-xs text-[var(--ink-faint)]">Aucune classe pour ce niveau.</p>
                  )}
                  <Input
                    label="Observations"
                    value={form.observation}
                    onChange={(e) => set('observation', e.target.value)}
                    placeholder="Remarques sur le dossier..."
                  />
                </div>
              )}

              {step === 4 && (
                <div className="space-y-3">
                  <p className="mb-2 text-xs text-[var(--ink-dim)]">
                    Cochez les documents fournis par la famille et importez les fichiers scannés.
                  </p>
                  {Object.entries(DOCS_LABELS).map(([field, label]) => {
                    const checked = form[field as keyof typeof form] as boolean
                    const file = docFiles[field] ?? null
                    const isActe = field === 'acte_naissance'
                    const acteCivilValide =
                      isActe &&
                      ((form.numero_acte.trim() || form.jugement_suppletif.trim()) &&
                        !!form.date_acte &&
                        !!form.delivre_par.trim())
                    return (
                      <div
                        key={field}
                        className="rounded-[var(--radius-sm)] border p-4 transition-all"
                        style={{
                          borderColor: checked ? 'var(--success)' : 'var(--border)',
                          background: checked ? 'var(--success-w)' : 'var(--surface)',
                        }}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <div
                              className="flex size-9 shrink-0 items-center justify-center rounded-[var(--radius-sm)]"
                              style={{ background: checked ? 'var(--success-w)' : 'var(--surface-2)' }}
                            >
                              {checked ? (
                                <CheckCircle size={18} className="text-[var(--success)]" />
                              ) : (
                                <FileText size={18} className="text-[var(--ink-faint)]" />
                              )}
                            </div>
                            <div>
                              <p className="text-[13px] font-medium text-[var(--ink)]">
                                {label}
                                <span aria-hidden="true" className="ml-1 text-[var(--danger)]">*</span>
                              </p>
                              <p className="text-[11px] text-[var(--ink-faint)]">
                                {checked ? 'Document reçu' : 'En attente de réception'}
                              </p>
                            </div>
                          </div>
                          <button
                            type="button"
                            onClick={() => set(field, !checked)}
                            disabled={isActe && !acteCivilValide && !checked}
                            className="rounded-[var(--radius-sm)] border px-3 py-1.5 text-xs font-medium transition-all disabled:cursor-not-allowed disabled:opacity-40"
                            style={{
                              background: checked ? 'var(--success-w)' : 'var(--surface)',
                              color: checked ? 'var(--success)' : 'var(--ink-dim)',
                              borderColor: checked ? 'var(--success)' : 'var(--border)',
                            }}
                          >
                            {checked ? 'Reçu' : 'Marquer reçu'}
                          </button>
                        </div>

                        {isActe && !checked && (
                          <div className="mt-4 space-y-3">
                            <p className="text-[11px] font-semibold text-[var(--ink-dim)]">
                              État civil à renseigner avant de marquer reçu :
                            </p>
                            <div className="grid grid-cols-2 gap-3">
                              <Input
                                label="Acte de naissance N°"
                                placeholder="ex. N° 1234/25"
                                value={form.numero_acte}
                                onChange={(e) => set('numero_acte', e.target.value)}
                              />
                              <Input
                                label="Jugement supplétif N°"
                                placeholder="ex. N° 567/25"
                                value={form.jugement_suppletif}
                                onChange={(e) => set('jugement_suppletif', e.target.value)}
                              />
                            </div>
                            <div className="grid grid-cols-2 gap-3">
                              <Input
                                label="Date de l'acte"
                                type="date"
                                value={form.date_acte}
                                onChange={(e) => set('date_acte', e.target.value)}
                              />
                              <Input
                                label="Délivré par"
                                placeholder="ex. Mairie de Bamako"
                                value={form.delivre_par}
                                onChange={(e) => set('delivre_par', e.target.value)}
                              />
                            </div>
                            {!acteCivilValide && (
                              <p className="flex items-center gap-1.5 text-[11px] text-[var(--info)]">
                                <AlertCircle size={12} strokeWidth={1.75} />
                                Renseignez un N° d'acte ou de jugement, la date et le délivrant pour activer « Marquer reçu ».
                              </p>
                            )}
                          </div>
                        )}

                        {canImport ? (
                          <div className="mt-3 flex items-center gap-3">
                            <label className="flex cursor-pointer items-center gap-2 rounded border border-[var(--border)] px-3 py-2 text-xs text-[var(--ink-dim)] hover:bg-[var(--surface-2)]">
                              <Upload size={14} strokeWidth={1.75} />
                              {file ? file.name : 'Importer le fichier…'}
                              <input
                                type="file"
                                accept=".pdf,.jpg,.jpeg,.png"
                                className="hidden"
                                onChange={(e) => {
                                  const f = e.target.files?.[0] ?? null
                                  setDocFiles((prev) => ({ ...prev, [field]: f }))
                                }}
                              />
                            </label>
                            {file && (
                              <button
                                type="button"
                                onClick={() => setDocFiles((prev) => ({ ...prev, [field]: null }))}
                                className="text-xs text-[var(--danger)] hover:underline"
                              >
                                Retirer
                              </button>
                            )}
                          </div>
                        ) : (
                          <p className="mt-3 text-[11px] text-[var(--ink-faint)]">
                            Les fichiers seront ajoutés par l'administrateur après la création de l'élève.
                          </p>
                        )}
                      </div>
                    )
                  })}
                  {uploadProgress && (
                    <div className="flex items-center gap-2 text-sm text-[var(--info)]">
                      <Upload size={14} strokeWidth={1.75} className="animate-pulse" />
                      {uploadProgress}
                    </div>
                  )}
                </div>
              )}

              {step === 5 && (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="rounded-[var(--radius-sm)] border border-[var(--border)] p-4">
                      <p className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-[var(--ink-faint)]">Élève</p>
                      <p className="text-[15px] font-semibold text-[var(--ink)]">{form.prenom} {form.nom}</p>
                      <p className="mt-1 text-xs text-[var(--ink-dim)]">Né(e) le {form.dateNaissance || '—'}</p>
                      <p className="text-xs text-[var(--ink-dim)]">{form.lieuNaissance || '—'}</p>
                    </div>
                    <div className="rounded-[var(--radius-sm)] border border-[var(--border)] p-4">
                      <p className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-[var(--ink-faint)]">Tuteur légal</p>
                      {tuteurMode === 'select' && tuteurId ? (
                        <p className="text-sm font-semibold text-[var(--ink)]">
                          {tuteurs.find((t) => t.id === Number(tuteurId))?.prenom}{' '}
                          {tuteurs.find((t) => t.id === Number(tuteurId))?.nom}
                        </p>
                      ) : (
                        <>
                          <p className="text-sm font-semibold text-[var(--ink)]">{form.tuteurPrenom} {form.tuteurNom}</p>
                          <p className="mt-1 text-xs text-[var(--ink-dim)]">{form.tuteurEmail || '—'}</p>
                          <p className="text-xs text-[var(--ink-dim)]">{form.tuteurTelephone || '—'}</p>
                          <p className="text-xs text-[var(--ink-dim)]">{form.tuteurAdresse || '—'}</p>
                        </>
                      )}
                    </div>
                    <div className="rounded-[var(--radius-sm)] border border-[var(--border)] p-4">
                      <p className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-[var(--ink-faint)]">Scolarité</p>
                      <p className="text-sm font-semibold text-[var(--ink)]">
                        {form.niveauId || 'Niveau non choisi'}
                        {form.classeId ? ` · ${classesDuNiveau.find((c) => c.id === Number(form.classeId))?.nom || ''}` : ' · À attribuer'}
                      </p>
                    </div>
                    <div className="rounded-[var(--radius-sm)] border border-[var(--border)] p-4">
                      <p className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-[var(--ink-faint)]">Documents</p>
                      <div className="space-y-1.5">
                        {Object.entries(DOCS_LABELS).map(([f, l]) => (
                          <div key={f} className="flex items-center gap-2">
                            {form[f as keyof typeof form] as boolean ? (
                              <Check className="size-3.5 text-[var(--success)]" strokeWidth={1.75} />
                            ) : (
                              <X className="size-3.5 text-[var(--danger)]" strokeWidth={1.75} />
                            )}
                            <span className="text-xs text-[var(--ink-dim)]">{l}</span>
                          </div>
                        ))}
                      </div>
                      {form.acte_naissance && (
                        <div className="mt-3 space-y-1 rounded-[var(--radius-sm)] border border-[var(--border)] bg-[var(--surface-2)] px-3 py-2.5">
                          <p className="text-[11px] font-semibold uppercase tracking-wide text-[var(--ink-faint)]">État civil</p>
                          <p className="text-[11.5px] text-[var(--ink-dim)]">
                            <span className="text-[var(--ink-faint)]">N° acte : </span>
                            {form.numero_acte || '—'}
                          </p>
                          <p className="text-[11.5px] text-[var(--ink-dim)]">
                            <span className="text-[var(--ink-faint)]">Jugement supplétif : </span>
                            {form.jugement_suppletif || '—'}
                          </p>
                          <p className="text-[11.5px] text-[var(--ink-dim)]">
                            <span className="text-[var(--ink-faint)]">Date de l'acte : </span>
                            {form.date_acte || '—'}
                          </p>
                          <p className="text-[11.5px] text-[var(--ink-dim)]">
                            <span className="text-[var(--ink-faint)]">Délivré par : </span>
                            {form.delivre_par || '—'}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                  {form.observation && (
                    <div className="rounded-[var(--radius-sm)] border border-[var(--warning)]/30 bg-[var(--warning-w)] px-3 py-2">
                      <p className="mb-1 text-[11px] font-semibold text-[var(--warning)]">OBSERVATIONS</p>
                      <p className="text-xs text-[var(--ink)]">{form.observation}</p>
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </div>

        {!submitted && (
          <div className="flex items-center justify-between border-t border-[var(--border)] bg-[var(--surface-2)] px-6 py-4">
            <p className="text-xs text-[var(--ink-faint)]">Étape {step} / {STEPS.length}</p>
            <div className="flex gap-2">
              <Button variant="ghost" onClick={onCancel}>Annuler</Button>
              {step > 1 && (
                <Button variant="secondary" onClick={() => setStep((s) => s - 1)}>
                  <ChevronLeft size={14} strokeWidth={1.75} /> Précédent
                </Button>
              )}
              {step < STEPS.length ? (
                <Button variant="primary" onClick={handleNext}>
                  Suivant <ChevronRight size={14} strokeWidth={1.75} />
                </Button>
              ) : (
                <Button variant="primary" onClick={handleSubmit} isLoading={submitting}>
                  <CheckCircle size={14} strokeWidth={1.75} /> Enregistrer l'inscription
                </Button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
