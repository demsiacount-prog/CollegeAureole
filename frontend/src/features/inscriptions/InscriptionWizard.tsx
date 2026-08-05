import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
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
import type { DossierCompletInput } from './api'

const DOCS_LABELS: Record<string, string> = {
  acte_naissance: 'Acte de naissance',
  carnet_sante: 'Carnet de santé',
  jugement_tutelle: 'Jugement de tutelle (si applicable)',
  photo_id: "Photo d'identité",
  certificat_radiation: 'Certificat de radiation',
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
}

const emptyForm = {
  nom: '', prenom: '', dateNaissance: '', lieuNaissance: '', sexe: 'M',
  tuteurNom: '', tuteurPrenom: '', tuteurEmail: '', tuteurTelephone: '', tuteurAdresse: '', tuteurProfession: '',
  niveauId: '', classeId: '', anneeScolaireId: '',
  acte_naissance: false, carnet_sante: false, jugement_tutelle: false, photo_id: false, certificat_radiation: false,
  observation: '',
}

const DOCS_FIELDS = ['acte_naissance', 'carnet_sante', 'jugement_tutelle', 'photo_id', 'certificat_radiation'] as const

export default function InscriptionWizard({ onComplete, onCancel }: Props) {
  const [step, setStep] = useState(1)
  const [form, setForm] = useState(emptyForm)
  const [tuteurMode, setTuteurMode] = useState<'create' | 'select'>('create')
  const [tuteurId, setTuteurId] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [submitted, setSubmitted] = useState(false)
  const [codeInscription, setCodeInscription] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
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

  async function handleSubmit() {
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
          jugement_tutelle: form.jugement_tutelle,
          photo_id: form.photo_id,
          certificat_radiation: form.certificat_radiation,
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
      const msg = err instanceof Error ? err.message : "Erreur lors de l'enregistrement."
      setError(msg)
      setSubmitting(false)
    }
  }

  return (
    <div className="flex gap-6">
      <div className="w-52 shrink-0">
        <div className="overflow-hidden rounded-[var(--radius-lg)] border border-[var(--color-border)] bg-[var(--color-surface)]">
          <div className="px-4 py-4">
            <p className="text-[13px] font-semibold text-[var(--color-ink)]">Nouvelle inscription</p>
            <p className="mb-3 text-[11px] text-[var(--color-ink-faint)]">
              {anneeActive?.libelle ?? 'Année scolaire'}
            </p>
            <div className="mb-4">
              <div className="mb-1 flex justify-between">
                <span className="text-[10px] text-[var(--color-ink-faint)]">Progression</span>
                <span className="text-[10px] text-[var(--color-ink-faint)]">{pct}%</span>
              </div>
              <div className="h-1.5 rounded-full bg-[var(--color-border-soft)]">
                <div
                  className="h-1.5 rounded-full bg-[var(--color-brand)] transition-all duration-500"
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
                    className="flex w-full items-center gap-3 rounded px-3 py-2.5 text-left transition-all"
                    style={{
                      background: active ? 'var(--color-surface-2)' : 'transparent',
                      cursor: done ? 'pointer' : 'default',
                    }}
                  >
                    <div
                      className="flex size-6 shrink-0 items-center justify-center rounded-full"
                      style={{
                        background: done ? 'var(--color-brand)' : active ? 'var(--color-surface)' : 'var(--color-border-soft)',
                      }}
                    >
                      {done ? (
                        <CheckCircle size={13} className="text-white" />
                      ) : (
                        <Icon size={13} className={active ? 'text-[var(--color-ink)]' : 'text-[var(--color-ink-faint)]'} />
                      )}
                    </div>
                    <span
                      className="text-xs"
                      style={{
                        fontWeight: active ? 600 : 400,
                        color: active ? 'var(--color-ink)' : done ? 'var(--color-ink-dim)' : 'var(--color-ink-faint)',
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

      <div className="flex-1 overflow-hidden rounded-[var(--radius-lg)] border border-[var(--color-border)] bg-[var(--color-surface)]">
        <div className="border-b border-[var(--color-border)] px-6 py-4">
          <p className="text-[15px] font-semibold text-[var(--color-ink)]">{STEPS[step - 1].label}</p>
          <p className="text-xs text-[var(--color-ink-dim)]">Étape {step} sur {STEPS.length}</p>
        </div>

        <div className="px-6 py-6">
          {error && (
            <div className="mb-4 flex items-start gap-2 rounded-[var(--radius-sm)] border border-[var(--color-danger)]/30 bg-[var(--color-danger-wash)] px-3 py-2 text-sm text-[var(--color-danger)]">
              <AlertCircle size={14} className="mt-0.5 shrink-0" />
              {error}
            </div>
          )}

          {submitted ? (
            <div className="flex flex-col items-center justify-center gap-4 py-12">
              <div className="flex size-16 items-center justify-center rounded-full bg-[var(--color-success-wash)]">
                <CheckCircle size={36} className="text-[var(--color-success)]" />
              </div>
              <p className="text-lg font-semibold text-[var(--color-ink)]">Inscription enregistrée.</p>
              {codeInscription && (
                <p className="font-[var(--font-mono)] text-sm text-[var(--color-brand-blue)]">{codeInscription}</p>
              )}
              <p className="text-center text-sm text-[var(--color-ink-dim)]">
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
                    <Input label="Nom" placeholder="Traoré" value={form.nom} onChange={(e) => set('nom', e.target.value)} required />
                    <Input label="Prénom" placeholder="Fatoumata" value={form.prenom} onChange={(e) => set('prenom', e.target.value)} required />
                    <Input label="Date de naissance" type="date" value={form.dateNaissance} onChange={(e) => set('dateNaissance', e.target.value)} max={new Date().toISOString().split('T')[0]} required />
                  </div>
                  <Input label="Lieu de naissance" placeholder="Bamako" value={form.lieuNaissance} onChange={(e) => set('lieuNaissance', e.target.value)} />
                  <div className="flex items-start gap-2 rounded-[var(--radius-sm)] border border-[var(--color-info)]/30 bg-[var(--color-info-wash)] px-3 py-2">
                    <AlertCircle size={14} className="mt-0.5 shrink-0 text-[var(--color-info)]" />
                    <span className="text-xs text-[var(--color-info)]">
                      Les champs marqués * sont obligatoires.
                    </span>
                  </div>
                </div>
              )}

              {step === 2 && (
                <div className="space-y-4">
                  <div className="flex items-center gap-3 rounded-[var(--radius-sm)] border border-[var(--color-border-soft)] bg-[var(--color-surface-2)] p-3">
                    <button
                      type="button"
                      onClick={() => { setTuteurMode('select'); setTuteurId('') }}
                      className="rounded px-3 py-1.5 text-xs font-medium transition-all"
                      style={{
                        background: tuteurMode === 'select' ? 'var(--color-brand)' : 'var(--color-surface)',
                        color: tuteurMode === 'select' ? '#fff' : 'var(--color-ink-dim)',
                      }}
                    >
                      Tuteur existant
                    </button>
                    <button
                      type="button"
                      onClick={() => setTuteurMode('create')}
                      className="rounded px-3 py-1.5 text-xs font-medium transition-all"
                      style={{
                        background: tuteurMode === 'create' ? 'var(--color-brand)' : 'var(--color-surface)',
                        color: tuteurMode === 'create' ? '#fff' : 'var(--color-ink-dim)',
                      }}
                    >
                      Nouveau tuteur
                    </button>
                  </div>

                  {tuteurMode === 'select' ? (
                    <SearchableSelect
                      label="Choisir un tuteur"
                      value={tuteurId}
                      onChange={setTuteurId}
                      options={tuteurs.map((t) => ({
                        value: String(t.id),
                        label: `${t.prenom} ${t.nom}`.trim(),
                        sublabel: t.telephone,
                      }))}
                      placeholder="Rechercher un tuteur…"
                      emptyMessage="Aucun tuteur trouvé"
                    />
                  ) : (
                    <>
                      <div className="grid grid-cols-2 gap-4">
                        <Input label="Nom du tuteur" placeholder="Touré" value={form.tuteurNom} onChange={(e) => set('tuteurNom', e.target.value)} required />
                        <Input label="Prénom du tuteur" placeholder="Amadou" value={form.tuteurPrenom} onChange={(e) => set('tuteurPrenom', e.target.value)} required />
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        <Input label="Email" type="email" placeholder="amadou@email.com" value={form.tuteurEmail} onChange={(e) => set('tuteurEmail', e.target.value)} required />
                        <Input label="Téléphone" placeholder="+223 XX XX XX XX" value={form.tuteurTelephone} onChange={(e) => set('tuteurTelephone', e.target.value)} required />
                      </div>
                      <Input label="Adresse" placeholder="Badalabougou, Bamako" value={form.tuteurAdresse} onChange={(e) => set('tuteurAdresse', e.target.value)} required />
                      <Input label="Profession" placeholder="ex. Commerçant" value={form.tuteurProfession} onChange={(e) => set('tuteurProfession', e.target.value)} required />
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
                      <p className="mb-2 text-xs font-semibold text-[var(--color-ink)]">
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
                              background: Number(form.classeId) === c.id ? 'var(--color-info-wash)' : 'var(--color-surface)',
                              borderColor: Number(form.classeId) === c.id ? 'var(--color-info)' : 'var(--color-border)',
                            }}
                          >
                            <p className="text-sm font-semibold" style={{ color: Number(form.classeId) === c.id ? 'var(--color-info)' : 'var(--color-ink)' }}>
                              {c.niveau} — {c.nom}
                            </p>
                            <p className="text-[11px] text-[var(--color-ink-faint)]">
                              Salle
                            </p>
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  {!loadingClasses && classesDuNiveau.length === 0 && form.niveauId && (
                    <p className="text-xs text-[var(--color-ink-faint)]">Aucune classe pour ce niveau.</p>
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
                  <p className="mb-2 text-xs text-[var(--color-ink-dim)]">
                    Cochez les documents fournis par la famille et importez les fichiers scannés.
                  </p>
                  {Object.entries(DOCS_LABELS).map(([field, label]) => {
                    const checked = form[field as keyof typeof form] as boolean
                    const file = docFiles[field] ?? null
                    return (
                      <div
                        key={field}
                        className="rounded-[var(--radius-sm)] border p-4 transition-all"
                        style={{
                          borderColor: checked ? 'var(--color-success)' : 'var(--color-border)',
                          background: checked ? 'var(--color-success-wash)' : 'var(--color-surface)',
                        }}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <div
                              className="flex size-9 shrink-0 items-center justify-center rounded"
                              style={{ background: checked ? 'var(--color-success-wash)' : 'var(--color-surface-2)' }}
                            >
                              {checked ? (
                                <CheckCircle size={18} className="text-[var(--color-success)]" />
                              ) : (
                                <FileText size={18} className="text-[var(--color-ink-faint)]" />
                              )}
                            </div>
                            <div>
                              <p className="text-[13px] font-medium text-[var(--color-ink)]">
                                {label}
                                {field !== 'jugement_tutelle' && <span className="ml-1 text-[var(--color-danger)]">*</span>}
                              </p>
                              <p className="text-[11px] text-[var(--color-ink-faint)]">
                                {checked ? 'Document reçu' : 'En attente de réception'}
                              </p>
                            </div>
                          </div>
                          <button
                            type="button"
                            onClick={() => set(field, !checked)}
                            className="rounded border px-3 py-1.5 text-xs font-medium transition-all"
                            style={{
                              background: checked ? 'var(--color-success-wash)' : 'var(--color-surface)',
                              color: checked ? 'var(--color-success)' : 'var(--color-ink-dim)',
                              borderColor: checked ? 'var(--color-success)' : 'var(--color-border)',
                            }}
                          >
                            {checked ? 'Reçu' : 'Marquer reçu'}
                          </button>
                        </div>
                        <div className="mt-3 flex items-center gap-3">
                          <label className="flex cursor-pointer items-center gap-2 rounded border border-[var(--color-border)] px-3 py-2 text-xs text-[var(--color-ink-dim)] hover:bg-[var(--color-surface-2)]">
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
                              className="text-xs text-[var(--color-danger)] hover:underline"
                            >
                              Retirer
                            </button>
                          )}
                        </div>
                      </div>
                    )
                  })}
                  {uploadProgress && (
                    <div className="flex items-center gap-2 text-sm text-[var(--color-info)]">
                      <Upload size={14} strokeWidth={1.75} className="animate-pulse" />
                      {uploadProgress}
                    </div>
                  )}
                </div>
              )}

              {step === 5 && (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="rounded-[var(--radius-sm)] border border-[var(--color-border)] p-4">
                      <p className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-[var(--color-ink-faint)]">Élève</p>
                      <p className="text-[15px] font-semibold text-[var(--color-ink)]">{form.prenom} {form.nom}</p>
                      <p className="mt-1 text-xs text-[var(--color-ink-dim)]">Né(e) le {form.dateNaissance || '—'}</p>
                      <p className="text-xs text-[var(--color-ink-dim)]">{form.lieuNaissance || '—'}</p>
                    </div>
                    <div className="rounded-[var(--radius-sm)] border border-[var(--color-border)] p-4">
                      <p className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-[var(--color-ink-faint)]">Tuteur légal</p>
                      {tuteurMode === 'select' && tuteurId ? (
                        <p className="text-sm font-semibold text-[var(--color-ink)]">
                          {tuteurs.find((t) => t.id === Number(tuteurId))?.prenom}{' '}
                          {tuteurs.find((t) => t.id === Number(tuteurId))?.nom}
                        </p>
                      ) : (
                        <>
                          <p className="text-sm font-semibold text-[var(--color-ink)]">{form.tuteurPrenom} {form.tuteurNom}</p>
                          <p className="mt-1 text-xs text-[var(--color-ink-dim)]">{form.tuteurEmail || '—'}</p>
                          <p className="text-xs text-[var(--color-ink-dim)]">{form.tuteurTelephone || '—'}</p>
                          <p className="text-xs text-[var(--color-ink-dim)]">{form.tuteurAdresse || '—'}</p>
                        </>
                      )}
                    </div>
                    <div className="rounded-[var(--radius-sm)] border border-[var(--color-border)] p-4">
                      <p className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-[var(--color-ink-faint)]">Scolarité</p>
                      <p className="text-sm font-semibold text-[var(--color-ink)]">
                        {form.niveauId || 'Niveau non choisi'}
                        {form.classeId ? ` · ${classesDuNiveau.find((c) => c.id === Number(form.classeId))?.nom || ''}` : ' · À attribuer'}
                      </p>
                    </div>
                    <div className="rounded-[var(--radius-sm)] border border-[var(--color-border)] p-4">
                      <p className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-[var(--color-ink-faint)]">Documents</p>
                      <div className="space-y-1.5">
                        {Object.entries(DOCS_LABELS).map(([f, l]) => (
                          <div key={f} className="flex items-center gap-2">
                            {form[f as keyof typeof form] as boolean ? (
                              <Check className="size-3.5 text-[var(--color-success)]" strokeWidth={1.75} />
                            ) : (
                              <X className="size-3.5 text-[var(--color-danger)]" strokeWidth={1.75} />
                            )}
                            <span className="text-xs text-[var(--color-ink-dim)]">{l}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                  {form.observation && (
                    <div className="rounded-[var(--radius-sm)] border border-[var(--color-warning)]/30 bg-[var(--color-warning-wash)] px-3 py-2">
                      <p className="mb-1 text-[11px] font-semibold text-[var(--color-warning)]">OBSERVATIONS</p>
                      <p className="text-xs text-[var(--color-ink)]">{form.observation}</p>
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </div>

        {!submitted && (
          <div className="flex items-center justify-between border-t border-[var(--color-border)] bg-[var(--color-surface-2)] px-6 py-4">
            <p className="text-xs text-[var(--color-ink-faint)]">Étape {step} / {STEPS.length}</p>
            <div className="flex gap-2">
              <Button variant="ghost" onClick={onCancel}>Annuler</Button>
              {step > 1 && (
                <Button variant="secondary" onClick={() => setStep((s) => s - 1)}>
                  <ChevronLeft size={14} strokeWidth={1.75} /> Précédent
                </Button>
              )}
              {step < STEPS.length ? (
                <Button variant="primary" onClick={() => setStep((s) => s + 1)}>
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
