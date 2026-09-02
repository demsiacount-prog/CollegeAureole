import { useEffect, useMemo, useRef, useState, type ChangeEvent, type FormEvent } from 'react'
import { AnimatePresence, motion, useReducedMotion } from 'framer-motion'
import {
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  Eye,
  EyeOff,
  GraduationCap,
  ImagePlus,
  KeyRound,
  Loader2,
  Moon,
  RotateCcw,
  Sun,
  Trash2,
  XCircle,
} from 'lucide-react'
import { api, extractErrorMessage, TOKEN_STORAGE_KEY } from '@/lib/api'
import { urlAbsolue } from '@/lib/server'
import type { TokenResponse } from '@/types'
import { uploadSetupLogo } from '@/features/etablissement/api'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { useTheme } from '@/hooks/useTheme'
import { clsx } from 'clsx'
import {
  required, minLength, email as emailVal, phone,
  dateFinApresDebut, validateFields, hasErrors, type Errors,
} from '@/lib/validation'

type WizardStep = 'checking' | 'configured' | 'form' | 'running'
type FormStep = 1 | 2 | 3

interface Progress {
  run_id: string | null
  en_cours: boolean
  etape: number
  nb_etapes: number
  message: string
  pourcent: number
  termine: boolean
  erreur: string | null
}

interface SetupStatus {
  configured: boolean
  progression: Progress | null
}

const FORM_STEPS = [
  { n: 1, label: 'Établissement' },
  { n: 2, label: 'Compte admin' },
  { n: 3, label: 'Année scolaire' },
]

function anneeScolaireParDefaut() {
  const now = new Date()
  const annee = now.getFullYear()
  if (now.getMonth() >= 9) {
    return { date_debut: `${annee}-10-01`, date_fin: `${annee + 1}-07-31` }
  }
  return { date_debut: `${annee - 1}-10-01`, date_fin: `${annee}-07-31` }
}

function StepIndicator({ current }: { current: number }) {
  const items = [...FORM_STEPS, { n: 4, label: 'Initialisation' }]
  return (
    <ol className="mb-8 flex items-center">
      {items.map((it, i) => {
        const done = current > it.n
        const active = current === it.n
        return (
          <li key={it.n} className={clsx('flex items-center', i > 0 && 'flex-1')}>
            {i > 0 && (
              <span
                className={clsx(
                  'mx-2 h-px flex-1 transition-colors duration-500',
                  done ? 'bg-[var(--color-action)]' : 'bg-[var(--color-border)]',
                )}
              />
            )}
            <div className="flex flex-col items-center gap-1">
              <span
                className={clsx(
                  'inline-flex h-6 w-6 items-center justify-center rounded-full text-[11px] font-medium transition-all duration-300',
                  done && 'bg-[var(--color-action)] text-white',
                  active && 'bg-[var(--color-action-wash)] text-[var(--color-action)] ring-2 ring-[var(--color-action)]',
                  !done && !active && 'bg-[var(--color-surface-3)] text-[var(--color-ink-faint)]',
                )}
              >
                {done ? <CheckCircle2 className="size-3.5" /> : it.n}
              </span>
              <span
                className={clsx(
                  'hidden whitespace-nowrap text-xs font-medium sm:block',
                  done || active ? 'text-[var(--color-ink)]' : 'text-[var(--color-ink-faint)]',
                )}
              >
                {it.label}
              </span>
            </div>
          </li>
        )
      })}
    </ol>
  )
}

export default function SetupWizard() {
  const { theme, toggle: toggleTheme } = useTheme()
  const reduce = useReducedMotion()
  const [step, setStep] = useState<WizardStep>('checking')
  const [formStep, setFormStep] = useState<FormStep>(1)

  // Fiche établissement
  const [etNom, setEtNom] = useState('')
  const [etSigle, setEtSigle] = useState('')
  const [etDevise, setEtDevise] = useState('')
  const [etAdresse, setEtAdresse] = useState('')
  const [etTelephone, setEtTelephone] = useState('')
  const [etEmail, setEtEmail] = useState('')
  const [etAcademie, setEtAcademie] = useState('')
  const [etCap, setEtCap] = useState('')
  const [etLogo, setEtLogo] = useState('')
  const logoFileRef = useRef<HTMLInputElement>(null)
  const [logoUploading, setLogoUploading] = useState(false)

  // Compte administrateur
  const [nom, setNom] = useState('')
  const [prenom, setPrenom] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPwd, setShowPwd] = useState(false)

  // Année scolaire
  const defaut = useMemo(anneeScolaireParDefaut, [])
  const [dateDebut, setDateDebut] = useState(defaut.date_debut)
  const [dateFin, setDateFin] = useState(defaut.date_fin)
  const [error, setError] = useState('')
  const [fieldErrors, setFieldErrors] = useState<Errors>({})
  const [progress, setProgress] = useState<Progress | null>(null)
  const runIdRef = useRef<string | null>(null)
  const autoLoginRef = useRef(false)

  // ── État initial ──────────────────────────────────────────────────────────
  useEffect(() => {
    api.get<SetupStatus>('/api/setup/status')
      .then((res) => {
        if (res.data.configured) {
          setStep('configured')
        } else if (res.data.progression?.en_cours) {
          setProgress(res.data.progression)
          setStep('running')
        } else {
          setStep('form')
        }
      })
      .catch(() => setStep('form'))
  }, [])

  // ── Progression (polling tant que l'initialisation tourne) ────────────────
  useEffect(() => {
    if (step !== 'running') return
    let cancelled = false
    const poll = () => {
      api.get<Progress>('/api/setup/progress')
        .then((res) => {
          if (cancelled) return
          setProgress(res.data)
        })
        .catch(() => {
          if (!cancelled) {
            setProgress((prev) => prev ? { ...prev, erreur: 'Progression indisponible.' } : null)
          }
        })
    }
    const timer = setInterval(poll, 1500)
    poll()
    return () => {
      cancelled = true
      clearInterval(timer)
    }
  }, [step])

  // ── Auto-connexion de l'administrateur à la fin de l'initialisation ─────
  // L'écran de succès (avec « Se connecter ») reste le filet de sécurité si la
  // connexion automatique échoue.
  useEffect(() => {
    if (step !== 'running') return
    if (progress?.termine !== true || progress?.erreur != null) return
    if (autoLoginRef.current) return
    autoLoginRef.current = true
    api
      .post<TokenResponse>('/api/auth/connexion', { email, mot_de_passe: password })
      .then((res) => {
        localStorage.setItem(TOKEN_STORAGE_KEY, res.data.access_token)
        window.location.href = '/app'
      })
      .catch(() => {
        // Silencieux : l'utilisateur peut toujours se connecter via l'écran de succès.
      })
  }, [step, progress, email, password])

  async function handleLogoChange(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    e.target.value = ''
    if (!file) return
    if (!file.type.startsWith('image/')) {
      setError('Veuillez choisir un fichier image (PNG, JPG, WebP ou GIF).')
      return
    }
    setLogoUploading(true)
    setError('')
    try {
      const path = await uploadSetupLogo(file)
      setEtLogo(path)
    } catch (err) {
      setError(extractErrorMessage(err, 'Erreur lors de l’import du logo.'))
    } finally {
      setLogoUploading(false)
    }
  }

  async function handleRun() {
    setError('')
    setFieldErrors({})
    setStep('running')
    setProgress({ run_id: null, en_cours: true, etape: 0, nb_etapes: 5, message: 'Initialisation lancée…', pourcent: 0, termine: false, erreur: null })
    try {
      const res = await api.post(
        '/api/setup/run',
        {
          etablissement: {
            nom: etNom.trim(),
            sigle: etSigle.trim() || null,
            devise: etDevise.trim() || null,
            adresse: etAdresse.trim() || null,
            telephone: etTelephone.trim() || null,
            email: etEmail.trim() || null,
            logo: etLogo || null,
            academie: etAcademie.trim() || null,
            cap: etCap.trim() || null,
          },
          admin: { nom: nom.trim(), prenom: prenom.trim(), email, mot_de_passe: password },
          annee_scolaire: { date_debut: dateDebut, date_fin: dateFin },
        },
        { timeout: 30_000 },
      )
      runIdRef.current = res.data.run_id
    } catch (err) {
      const message = extractErrorMessage(err, 'Erreur lors de la configuration.')
      if (message.includes('déjà configurée')) {
        window.location.href = '/connexion'
      } else if (message.includes('en cours')) {
        setError(message)
        setProgress({ run_id: null, en_cours: false, etape: 0, nb_etapes: 5, message: '', pourcent: 0, termine: true, erreur: message })
      } else {
        setError(message)
        setStep('form')
      }
    }
  }

  const etablissementValide =
    etNom.trim().length >= 2 &&
    etSigle.trim().length >= 1 &&
    etDevise.trim().length >= 1 &&
    etAdresse.trim().length >= 1 &&
    etTelephone.trim().length >= 1 &&
    etEmail.trim().length >= 1 &&
    emailVal(etEmail) === undefined &&
    phone(etTelephone) === undefined &&
    etAcademie.trim().length >= 1 &&
    etCap.trim().length >= 1 &&
    etLogo.trim().length >= 1
  const adminValide =
    nom.trim().length >= 2 && prenom.trim().length >= 2 &&
    emailVal(email) === undefined && password.length >= 8

  function validerEtape1(): boolean {
    const errs = validateFields({
      et_nom: required(etNom, "Le nom de l'établissement") ?? minLength(etNom, 2, "Le nom de l'établissement"),
      et_sigle: required(etSigle, 'Le sigle'),
      et_devise: required(etDevise, 'La devise'),
      et_adresse: required(etAdresse, 'L’adresse'),
      et_telephone: required(etTelephone, 'Le téléphone') ?? phone(etTelephone),
      et_email: required(etEmail, 'L’e-mail de contact') ?? emailVal(etEmail),
      et_academie: required(etAcademie, 'L’académie'),
      et_cap: required(etCap, 'Le CAP'),
      et_logo: required(etLogo, 'Le logo'),
    })
    setFieldErrors(errs)
    return !hasErrors(errs)
  }

  function validerEtape2(): boolean {
    const errs = validateFields({
      nom: required(nom, 'Le nom') ?? minLength(nom, 2, 'Le nom'),
      prenom: required(prenom, 'Le prénom') ?? minLength(prenom, 2, 'Le prénom'),
      email: required(email, "L'e-mail") ?? emailVal(email),
      mot_de_passe: required(password, 'Le mot de passe') ?? minLength(password, 8, 'Le mot de passe'),
    })
    setFieldErrors(errs)
    return !hasErrors(errs)
  }

  function validerEtape3(): boolean {
    const errs = validateFields({
      date_debut: required(dateDebut, 'La date de rentrée'),
      date_fin: required(dateFin, "La date de fin") ?? dateFinApresDebut(dateDebut, dateFin),
    })
    setFieldErrors(errs)
    return !hasErrors(errs)
  }

  function suivant(event: FormEvent) {
    event.preventDefault()
    if (formStep === 1 && validerEtape1()) setFormStep(2)
    else if (formStep === 2 && validerEtape2()) setFormStep(3)
  }

  function retourner() {
    setError('')
    if (formStep > 1) setFormStep((s) => (s - 1) as FormStep)
  }

  const runTerminee = progress?.termine === true
  const runEnEchec = runTerminee && progress?.erreur != null

  const activeStep = step === 'form' ? formStep : step === 'running' || step === 'configured' ? 4 : 0

  return (
    <div className="min-h-screen bg-[var(--color-base)] text-[var(--color-ink)]">
      <div className="grid min-h-screen lg:grid-cols-2">
        {/* ── Brand panel ─────────────────────────────────────────── */}
        <section className="relative hidden flex-col justify-between overflow-hidden border-r border-[var(--color-border)] bg-gradient-to-br from-[var(--color-surface)] via-[var(--color-base)] to-[var(--color-base)] p-12 lg:flex">
          <div className="pointer-events-none absolute -right-24 -top-24 h-96 w-96 rounded-full bg-[var(--color-mod-ress)]/10 blur-3xl" />
          <div className="pointer-events-none absolute -bottom-32 -left-24 h-80 w-80 rounded-full bg-[var(--color-mod-ress)]/10 blur-3xl" />

          <div className="relative flex items-center gap-3">
            {etLogo ? (
              <img
                src={urlAbsolue(etLogo)}
                alt="Logo de l’établissement"
                className="h-12 w-12 rounded-lg bg-[var(--color-surface-2)] object-contain p-1 ring-1 ring-[var(--color-border)]"
              />
            ) : (
              <span className="inline-flex h-12 w-12 items-center justify-center rounded-lg bg-[var(--color-action-wash)] text-[var(--color-action)] ring-1 ring-[var(--color-border)]">
                <GraduationCap className="h-6 w-6" />
              </span>
            )}
            <div>
              <p className="text-xl font-semibold text-[var(--color-halo)]">
                {etNom.trim()}
              </p>
              <p className="text-xs text-[var(--color-ink-dim)]">
                {etDevise.trim()}
              </p>
            </div>
          </div>

          <div className="relative">
            <h1 className="mb-4 max-w-md text-4xl font-semibold leading-tight tracking-tight">
              Prêt à piloter votre établissement&nbsp;?
            </h1>
            <p className="max-w-md text-sm leading-relaxed text-[var(--color-ink-dim)]">
              Renseignez la fiche de l’établissement, créez le compte administrateur
              puis choisissez l’année scolaire. L’initialisation est effectuée une
              seule fois, au premier lancement.
            </p>
          </div>

          <p className="relative text-xs text-[var(--color-ink-faint)]">
            © {new Date().getFullYear()} — Tous droits réservés.
          </p>
        </section>

        {/* ── Form panel ─────────────────────────────────────────── */}
        <section className="flex items-center justify-center px-6 py-10 sm:px-10">
          <div className="w-full max-w-md">
            {/* Mobile logo */}
            <div className="mb-8 flex items-center gap-3 lg:hidden">
              {etLogo ? (
                <img
                  src={urlAbsolue(etLogo)}
                  alt="Logo de l’établissement"
                  className="h-10 w-10 rounded-lg bg-[var(--color-surface-2)] object-contain p-1 ring-1 ring-[var(--color-border)]"
                />
              ) : (
                <span className="inline-flex h-10 w-10 items-center justify-center rounded-lg bg-[var(--color-action-wash)] text-[var(--color-action)] ring-1 ring-[var(--color-border)]">
                  <GraduationCap className="h-5 w-5" />
                </span>
              )}
              <div>
                <p className="text-base font-semibold text-[var(--color-halo)]">
                  {etNom.trim()}
                </p>
                <p className="text-xs text-[var(--color-ink-dim)]">
                  {etDevise.trim()}
                </p>
              </div>
            </div>

            {step === 'checking' && (
              <div className="flex items-center justify-center py-24">
                <Loader2 className="size-6 animate-spin text-[var(--color-action)]" />
              </div>
            )}

            {step === 'configured' && (
              <div className="rounded-[var(--radius-lg)] border border-[var(--color-border)] bg-[var(--color-surface)] p-8 text-center shadow-[var(--shadow-soft)]">
                <span className="mx-auto mb-5 inline-flex h-14 w-14 items-center justify-center rounded-full bg-[var(--color-success)] text-white">
                  <CheckCircle2 className="size-7" />
                </span>
                <h2 className="text-xl font-semibold text-[var(--color-ink)]">
                  Déjà configuré
                </h2>
                <p className="mt-1 text-sm text-[var(--color-ink-dim)]">
                  L’établissement a déjà été initialisé.
                </p>
                <Button
                  variant="primary"
                  href="/connexion"
                  className="mt-6"
                >
                  Se connecter
                  <ArrowRight className="size-4" />
                </Button>
              </div>
            )}

            {step === 'running' && (
              <div className="rounded-[var(--radius-lg)] border border-[var(--color-border)] bg-[var(--color-surface)] p-8 text-center shadow-[var(--shadow-soft)]">
                <StepIndicator current={activeStep} />
                {runEnEchec ? (
                  <div>
                    <span className="mx-auto mb-5 inline-flex h-14 w-14 items-center justify-center rounded-full bg-[var(--color-danger)] text-white">
                      <XCircle className="size-7" />
                    </span>
                    <h2 className="text-xl font-semibold text-[var(--color-ink)]">
                      Échec de l’initialisation
                    </h2>
                    <p className="mt-2 text-sm text-[var(--color-ink-dim)]">
                      {progress?.erreur}
                    </p>
                    <div className="mt-6 flex justify-center gap-3">
                      <Button
                        variant="ghost"
                        onClick={() => { setError(''); setStep('form'); setFormStep(1) }}
                      >
                        <RotateCcw className="size-4" />
                        Recommencer
                      </Button>
                      <Button variant="primary" onClick={handleRun}>
                        Réessayer
                      </Button>
                    </div>
                  </div>
                ) : runTerminee ? (
                  <div>
                    <span className="mx-auto mb-5 inline-flex h-14 w-14 items-center justify-center rounded-full bg-[var(--color-success)] text-white">
                      <CheckCircle2 className="size-7" />
                    </span>
                    <h2 className="text-xl font-semibold text-[var(--color-ink)]">
                      Initialisation terminée
                    </h2>
                    <p className="mt-2 text-sm text-[var(--color-ink-dim)]">
                      L’application est prête. Conservez précieusement vos identifiants.
                    </p>

                    <div className="mt-6 space-y-2 text-left">
                      <div className="rounded-[var(--radius-sm)] border border-[var(--color-border)] bg-[var(--color-surface-2)] p-3">
                        <div className="flex items-center gap-2 text-xs font-semibold text-[var(--color-ink)]">
                          <KeyRound className="size-3.5" />
                          Administrateur
                        </div>
                        <div className="mt-2 space-y-1 break-all font-mono text-xs text-[var(--color-ink-dim)]">
                          <p>E-mail : <span className="text-[var(--color-ink)]">{email}</span></p>
                          <p>Mot de passe : <span className="text-[var(--color-ink)]">{password}</span></p>
                        </div>
                      </div>
                    </div>

                    <Button variant="primary" href="/connexion" className="mt-6">
                      Se connecter
                      <ArrowRight className="size-4" />
                    </Button>
                  </div>
                ) : (
                  <div>
                    <div className="relative mx-auto mb-6 h-20 w-20">
                      <span className="absolute inset-0 animate-ping rounded-full bg-[var(--color-action)]/20" />
                      <span className="absolute inset-0 flex items-center justify-center rounded-full bg-[var(--color-action-wash)]">
                        <Loader2 className="size-8 animate-spin text-[var(--color-action)]" />
                      </span>
                    </div>
                    <h2 className="text-xl font-semibold text-[var(--color-ink)]">
                      Initialisation en cours
                    </h2>
                    <p className="mt-2 min-h-5 text-sm text-[var(--color-ink-dim)]">
                      {progress?.message || 'Veuillez patienter…'}
                    </p>
                    <div className="mt-8 h-1.5 w-full overflow-hidden rounded-full bg-[var(--color-surface-3)]">
                      <div
                        className="h-full rounded-full bg-[var(--color-action)] transition-all duration-500"
                        style={{ width: `${progress?.pourcent ?? 0}%` }}
                      />
                    </div>
                    <p className="mt-2 text-xs text-[var(--color-ink-faint)]">
                      Étape {progress?.etape ?? 0}/{progress?.nb_etapes ?? 5}
                    </p>
                  </div>
                )}
              </div>
            )}

            {step === 'form' && (
              <>
                <div className="rounded-[var(--radius-lg)] border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-[var(--shadow-soft)]">
                  <div className="mb-5 flex items-start justify-between">
                    <div>
                      <div className="mb-3 inline-flex h-9 w-9 items-center justify-center rounded-lg bg-[var(--color-action-wash)] text-[var(--color-action)]">
                        <GraduationCap className="h-4 w-4" />
                      </div>
                      <h2 className="text-2xl font-semibold tracking-tight text-[var(--color-ink)]">
                        {formStep === 1 && 'Configuration initiale'}
                        {formStep === 2 && 'Compte administrateur'}
                        {formStep === 3 && 'Année scolaire'}
                      </h2>
                      <p className="mt-1 text-sm text-[var(--color-ink-dim)]">
                        {formStep === 1 && 'Renseignez la fiche de votre établissement.'}
                        {formStep === 2 && 'Ce compte pilotera l\u2019ensemble de l\u2019application.'}
                        {formStep === 3 && 'Définissez la période scolaire.'}
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={toggleTheme}
                      className="rounded-md border border-[var(--color-border)] p-2 text-[var(--color-ink-dim)] transition-colors hover:bg-[var(--color-surface-2)]"
                      aria-label="Changer de thème"
                    >
                      {theme === 'dark' ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
                    </button>
                  </div>

                  <StepIndicator current={formStep} />

                  <form
                    onSubmit={(e) => {
                      e.preventDefault()
                      if (formStep < 3) {
                        suivant(e)
                      } else {
                        if (validerEtape3()) handleRun()
                      }
                    }}
                    className="flex flex-col gap-3"
                    noValidate
                  >
                    <AnimatePresence mode="wait">
                      {formStep === 1 && (
                        <motion.div
                          key="step-1"
                          initial={reduce ? undefined : { opacity: 0 }}
                          animate={{ opacity: 1 }}
                          exit={reduce ? undefined : { opacity: 0 }}
                          transition={{ duration: 0.2 }}
                        >
                        <div className="grid grid-cols-2 gap-3">
                          <Input
                            label="Nom de l’établissement"
                            type="text"
                            autoComplete="organization"
                            value={etNom}
                            onChange={(e) => {
                              setEtNom(e.target.value)
                              if (fieldErrors.et_nom) setFieldErrors((p) => ({ ...p, et_nom: undefined }))
                            }}
                            placeholder="Ex. Complexe Scolaire"
                            required
                            error={fieldErrors.et_nom}
                          />
                          <Input
                            label="Sigle"
                            type="text"
                            value={etSigle}
                            onChange={(e) => {
                              setEtSigle(e.target.value)
                              if (fieldErrors.et_sigle) setFieldErrors((p) => ({ ...p, et_sigle: undefined }))
                            }}
                            placeholder="Ex. CSX"
                            required
                            error={fieldErrors.et_sigle}
                          />
                          <Input
                            label="Devise"
                            type="text"
                            value={etDevise}
                            onChange={(e) => {
                              setEtDevise(e.target.value)
                              if (fieldErrors.et_devise) setFieldErrors((p) => ({ ...p, et_devise: undefined }))
                            }}
                            placeholder="Ex. Savoir, rigueur, réussite"
                            required
                            error={fieldErrors.et_devise}
                          />
                        </div>
                        <Input
                          label="Adresse"
                          type="text"
                          autoComplete="street-address"
                          value={etAdresse}
                          onChange={(e) => {
                            setEtAdresse(e.target.value)
                            if (fieldErrors.et_adresse) setFieldErrors((p) => ({ ...p, et_adresse: undefined }))
                          }}
                          placeholder="Ex. Quartier, ville"
                          required
                          error={fieldErrors.et_adresse}
                        />
                        <div className="grid grid-cols-2 gap-3">
                          <Input
                            label="Académie"
                            type="text"
                            value={etAcademie}
                            onChange={(e) => {
                              setEtAcademie(e.target.value)
                              if (fieldErrors.et_academie) setFieldErrors((p) => ({ ...p, et_academie: undefined }))
                            }}
                            placeholder="Ex. Académie de Kinshasa"
                            required
                            error={fieldErrors.et_academie}
                          />
                          <Input
                            label="CAP"
                            type="text"
                            value={etCap}
                            onChange={(e) => {
                              setEtCap(e.target.value)
                              if (fieldErrors.et_cap) setFieldErrors((p) => ({ ...p, et_cap: undefined }))
                            }}
                            placeholder="Ex. CA-0123"
                            required
                            error={fieldErrors.et_cap}
                          />
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                          <Input
                            label="Téléphone"
                            type="tel"
                            autoComplete="tel"
                            value={etTelephone}
                            onChange={(e) => {
                              setEtTelephone(e.target.value.replace(/[^+\d\s]/g, ''))
                              if (fieldErrors.et_telephone) setFieldErrors((p) => ({ ...p, et_telephone: undefined }))
                            }}
                            placeholder="+000 00 00 00 00"
                            required
                            error={fieldErrors.et_telephone}
                          />
                          <Input
                            label="E-mail de contact"
                            type="email"
                            value={etEmail}
                            onChange={(e) => {
                              setEtEmail(e.target.value)
                              if (fieldErrors.et_email) setFieldErrors((p) => ({ ...p, et_email: undefined }))
                            }}
                            placeholder="contact@etablissement.com"
                            required
                            error={fieldErrors.et_email}
                          />
                        </div>

                        <div>
                          <div className="mb-1 text-xs font-medium text-[var(--color-ink-dim)]">
                            Logo de l’établissement 
                          </div>
                          <input
                            ref={logoFileRef}
                            type="file"
                            accept="image/png,image/jpeg,image/webp,image/gif"
                            onChange={handleLogoChange}
                            className="hidden"
                          />
                          <button
                            type="button"
                            onClick={() => logoFileRef.current?.click()}
                            disabled={logoUploading}
                            className="flex w-full items-center gap-4 rounded-[var(--radius-sm)] border border-dashed border-[var(--color-border)] bg-[var(--color-surface-2)] p-4 text-left transition-colors hover:border-[var(--color-halo)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-halo)]"
                          >
                            {etLogo ? (
                              <img
                                src={urlAbsolue(etLogo)}
                                alt="Aperçu du logo"
                                className="h-14 w-14 shrink-0 rounded-lg bg-[var(--color-surface-3)] object-contain p-1 ring-1 ring-[var(--color-border)]"
                              />
                            ) : (
                              <span className="flex h-14 w-14 shrink-0 items-center justify-center rounded-lg border border-dashed border-[var(--color-border)] bg-[var(--color-surface-3)] text-[var(--color-ink-faint)]">
                                {logoUploading
                                  ? <Loader2 size={20} strokeWidth={1.75} className="animate-spin" />
                                  : <ImagePlus size={20} strokeWidth={1.75} />}
                              </span>
                            )}
                            <span className="min-w-0 flex-1">
                              <span className="block text-sm font-medium text-[var(--color-ink)]">
                                {logoUploading ? 'Envoi du logo…' : etLogo ? 'Modifier le logo' : 'Importer le logo de l’établissement'}
                              </span>
                              <span className="mt-0.5 block text-[11px] text-[var(--color-ink-faint)]">
                                PNG, JPG, WebP ou GIF — 2 Mo maximum. 
                              </span>
                            </span>
                            {etLogo && !logoUploading && (
                              <CheckCircle2 className="size-5 shrink-0 text-[var(--color-success)]" strokeWidth={1.75} />
                            )}
                          </button>
                          {etLogo && (
                            <div className="mt-2 flex justify-end">
                              <Button
                                type="button"
                                variant="ghost"
                                size="sm"
                                onClick={() => {
                                  setEtLogo('')
                                  if (fieldErrors.et_logo) setFieldErrors((p) => ({ ...p, et_logo: undefined }))
                                }}
                              >
                                <Trash2 size={14} strokeWidth={1.75} className="mr-1.5" />
                                Retirer le logo
                              </Button>
                            </div>
                          )}
                          {fieldErrors.et_logo && (
                            <p className="mt-1 text-xs text-[var(--color-danger)]">{fieldErrors.et_logo}</p>
                          )}
                        </div>
                        </motion.div>
                      )}

                      {formStep === 2 && (
                        <motion.div
                          key="step-2"
                          initial={reduce ? undefined : { opacity: 0 }}
                          animate={{ opacity: 1 }}
                          exit={reduce ? undefined : { opacity: 0 }}
                          transition={{ duration: 0.2 }}
                        >
                        <div className="grid grid-cols-2 gap-3">
                          <Input
                            label="Nom"
                            type="text"
                            autoComplete="family-name"
                            value={nom}
                            onChange={(e) => {
                              setNom(e.target.value)
                              if (fieldErrors.nom) setFieldErrors((p) => ({ ...p, nom: undefined }))
                            }}
                            required
                            error={fieldErrors.nom}
                          />
                          <Input
                            label="Prénom"
                            type="text"
                            autoComplete="given-name"
                            value={prenom}
                            onChange={(e) => {
                              setPrenom(e.target.value)
                              if (fieldErrors.prenom) setFieldErrors((p) => ({ ...p, prenom: undefined }))
                            }}
                            required
                            error={fieldErrors.prenom}
                          />
                        </div>

                        <Input
                          label="Adresse e-mail administrateur"
                          type="email"
                          autoComplete="email"
                          value={email}
                          onChange={(e) => {
                            setEmail(e.target.value)
                            if (fieldErrors.email) setFieldErrors((p) => ({ ...p, email: undefined }))
                          }}
                          hint="Cet e-mail sera utilisé pour vous connecter."
                          required
                          error={fieldErrors.email}
                        />

                        <div className="flex flex-col gap-1.5">
                          <label htmlFor="setup-password" className="text-sm font-medium text-[var(--color-ink-dim)]">
                            Mot de passe
                          </label>
                          <div className="relative">
                            <input
                              id="setup-password"
                              value={password}
                              onChange={(e) => {
                                setPassword(e.target.value)
                                if (fieldErrors.mot_de_passe) setFieldErrors((p) => ({ ...p, mot_de_passe: undefined }))
                              }}
                              type={showPwd ? 'text' : 'password'}
                              autoComplete="new-password"
                              required
                              minLength={8}
                              className={clsx(
                                'h-10 w-full rounded-[var(--radius-sm)] border bg-[var(--color-surface-2)] px-3 pr-10 text-sm text-[var(--color-ink)] outline-none transition-colors duration-150 focus-visible:border-[var(--color-halo)] focus-visible:ring-2 focus-visible:ring-[var(--color-halo)]',
                                fieldErrors.mot_de_passe ? 'border-[var(--color-danger)]' : 'border-[var(--color-border)]',
                              )}
                            />
                            <button
                              type="button"
                              onClick={() => setShowPwd((v) => !v)}
                              className="absolute right-2 top-1/2 -translate-y-1/2 rounded-md p-1 text-[var(--color-ink-dim)] transition-colors hover:bg-[var(--color-surface-3)]"
                              aria-label={showPwd ? 'Masquer le mot de passe' : 'Afficher le mot de passe'}
                            >
                              {showPwd ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                            </button>
                          </div>
                          {fieldErrors.mot_de_passe ? (
                            <p className="text-xs text-[var(--color-danger)]">{fieldErrors.mot_de_passe}</p>
                          ) : (
                            <p className="text-xs text-[var(--color-ink-faint)]">
                              Au moins 8 caractères.
                            </p>
                          )}
                        </div>
                        </motion.div>
                      )}

                      {formStep === 3 && (
                        <motion.div
                          key="step-3"
                          initial={reduce ? undefined : { opacity: 0 }}
                          animate={{ opacity: 1 }}
                          exit={reduce ? undefined : { opacity: 0 }}
                          transition={{ duration: 0.2 }}
                        >
                        <div className="grid grid-cols-2 gap-3">
                          <div className="flex flex-col gap-1.5">
                            <label htmlFor="date-debut" className="text-sm font-medium text-[var(--color-ink-dim)]">
                              Rentrée
                            </label>
                            <input
                              id="date-debut"
                              type="date"
                              value={dateDebut}
                              onChange={(e) => {
                                setDateDebut(e.target.value)
                                if (fieldErrors.date_debut) setFieldErrors((p) => ({ ...p, date_debut: undefined }))
                              }}
                              className={clsx(
                                'h-10 w-full rounded-[var(--radius-sm)] border bg-[var(--color-surface-2)] px-3 text-sm text-[var(--color-ink)] outline-none transition-colors duration-150 focus-visible:border-[var(--color-halo)] focus-visible:ring-2 focus-visible:ring-[var(--color-halo)]',
                                fieldErrors.date_debut ? 'border-[var(--color-danger)]' : 'border-[var(--color-border)]',
                              )}
                            />
                            {fieldErrors.date_debut && (
                              <p className="text-xs text-[var(--color-danger)]">{fieldErrors.date_debut}</p>
                            )}
                          </div>
                          <div className="flex flex-col gap-1.5">
                            <label htmlFor="date-fin" className="text-sm font-medium text-[var(--color-ink-dim)]">
                              Fin d’année
                            </label>
                            <input
                              id="date-fin"
                              type="date"
                              value={dateFin}
                              onChange={(e) => {
                                setDateFin(e.target.value)
                                if (fieldErrors.date_fin) setFieldErrors((p) => ({ ...p, date_fin: undefined }))
                              }}
                              className={clsx(
                                'h-10 w-full rounded-[var(--radius-sm)] border bg-[var(--color-surface-2)] px-3 text-sm text-[var(--color-ink)] outline-none transition-colors duration-150 focus-visible:border-[var(--color-halo)] focus-visible:ring-2 focus-visible:ring-[var(--color-halo)]',
                                fieldErrors.date_fin ? 'border-[var(--color-danger)]' : 'border-[var(--color-border)]',
                              )}
                            />
                            {fieldErrors.date_fin && (
                              <p className="text-xs text-[var(--color-danger)]">{fieldErrors.date_fin}</p>
                            )}
                          </div>
                        </div>
                        </motion.div>
                      )}
                    </AnimatePresence>

                    {error && (
                      <p
                        role="alert"
                        className="rounded-[var(--radius-sm)] border border-[var(--color-danger)]/30 bg-[var(--color-danger-wash)] px-3 py-2 text-sm text-[var(--color-danger)]"
                      >
                        {error}
                      </p>
                    )}

                    <div className="mt-2 flex gap-3">
                      {formStep > 1 && (
                        <Button variant="ghost" onClick={retourner} type="button">
                          <ArrowLeft className="size-4" />
                          Retour
                        </Button>
                      )}
                      {formStep < 3 ? (
                        <Button
                          type="submit"
                          variant="primary"
                          size="md"
                          disabled={formStep === 1 ? !etablissementValide : !adminValide}
                          className="flex-1"
                        >
                          Continuer
                          <ArrowRight className="size-4" />
                        </Button>
                      ) : (
                        <Button
                          type="submit"
                          variant="primary"
                          size="md"
                          className="flex-1"
                        >
                          Initialiser l’établissement
                          <ArrowRight className="size-4" />
                        </Button>
                      )}
                    </div>
                  </form>
                </div>

                <p className="mt-8 text-center text-xs text-[var(--color-ink-faint)]">
                  Les données sont stockées localement sur cet appareil.
                </p>
              </>
            )}
          </div>
        </section>
      </div>
    </div>
  )
}
