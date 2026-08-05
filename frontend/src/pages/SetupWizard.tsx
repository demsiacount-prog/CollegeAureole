import { useState, useEffect, type FormEvent } from 'react'
import {
  ArrowRight,
  CheckCircle2,
  Eye,
  EyeOff,
  GraduationCap,
  Loader2,
  Moon,
  Sun,
} from 'lucide-react'
import { api, extractErrorMessage } from '@/lib/api'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { useTheme } from '@/hooks/useTheme'
import { clsx } from 'clsx'

type Step = 'checking' | 'configured' | 'form' | 'seeding'

const MESSAGES = [
  'Création des comptes...',
  'Génération des élèves et enseignants...',
  'Création des notes et bulletins...',
  'Génération des paiements et absences...',
  'Presque terminé...',
]

const STEP_ITEMS = [
  { n: 1, label: 'Compte' },
  { n: 2, label: 'Données' },
  { n: 3, label: 'Initialisation' },
]

function StepIndicator({ current }: { current: number }) {
  return (
    <ol className="mb-8 flex items-center">
      {STEP_ITEMS.map((it, i) => {
        const done = current > it.n
        const active = current === it.n
        return (
          <li key={it.n} className={clsx('flex items-center', i > 0 && 'flex-1')}>
            {i > 0 && (
              <span
                className={clsx(
                  'mx-2 h-px flex-1 transition-colors duration-500',
                  done ? 'bg-[var(--color-brand)]' : 'bg-[var(--color-border)]',
                )}
              />
            )}
            <div className="flex items-center gap-2">
              <span
                className={clsx(
                  'inline-flex h-6 w-6 items-center justify-center rounded-full text-[11px] font-medium transition-all duration-300',
                  done && 'bg-[var(--color-brand)] text-white',
                  active && 'bg-[var(--color-brand-wash)] text-[var(--color-brand)] ring-2 ring-[var(--color-brand)]',
                  !done && !active && 'bg-[var(--color-surface-3)] text-[var(--color-ink-faint)]',
                )}
              >
                {done ? <CheckCircle2 className="size-3.5" /> : it.n}
              </span>
              <span
                className={clsx(
                  'text-xs font-medium',
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
  const [step, setStep] = useState<Step>('checking')
  const [nom, setNom] = useState('')
  const [prenom, setPrenom] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPwd, setShowPwd] = useState(false)
  const [seedData, setSeedData] = useState(true)
  const [error, setError] = useState('')
  const [progress, setProgress] = useState('')

  useEffect(() => {
    if (step !== 'seeding') return
    const timer = setInterval(() => {
      setProgress((prev) => {
        const idx = MESSAGES.indexOf(prev)
        return MESSAGES[(idx + 1) % MESSAGES.length]
      })
    }, 6000)
    return () => clearInterval(timer)
  }, [step])

  useEffect(() => {
    api.get<{ configured: boolean }>('/api/setup/status')
      .then((res) => setStep(res.data.configured ? 'configured' : 'form'))
      .catch(() => setStep('form'))
  }, [])

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError('')
    setStep('seeding')
    setProgress(MESSAGES[0])
    try {
      await api.post(
        '/api/setup/run',
        { nom, prenom, email, mot_de_passe: password, seed_data: seedData },
        { timeout: 600_000 },
      )
      setProgress('Configuration terminée, redirection...')
      window.location.href = '/connexion'
    } catch (err) {
      setError(extractErrorMessage(err, 'Erreur lors de la configuration.'))
      setStep('form')
    }
  }

  const activeStep = step === 'form' ? 1 : step === 'seeding' || step === 'configured' ? 3 : 0

  return (
    <div className="min-h-screen bg-[var(--color-base)] text-[var(--color-ink)]">
      <div className="grid min-h-screen lg:grid-cols-2">
        {/* ── Brand panel ─────────────────────────────────────────── */}
        <section className="relative hidden flex-col justify-between overflow-hidden border-r border-[var(--color-border)] bg-gradient-to-br from-[var(--color-surface)] via-[var(--color-base)] to-[var(--color-base)] p-12 lg:flex">
          <div className="pointer-events-none absolute -right-24 -top-24 h-96 w-96 rounded-full bg-[var(--color-brand-blue)]/10 blur-3xl" />
          <div className="pointer-events-none absolute -bottom-32 -left-24 h-80 w-80 rounded-full bg-[var(--color-brand-blue)]/10 blur-3xl" />

          <div className="relative flex items-center gap-3">
            <img
              src="/logo-aureole.jpeg"
              alt="Logo"
              className="h-12 w-12 rounded-lg object-cover ring-1 ring-[var(--color-border)]"
            />
            <div>
              <p className="text-xl font-semibold text-[var(--color-halo)]">
                Collège Auréole
              </p>
              <p className="text-xs text-[var(--color-ink-dim)]">
                Système de Gestion Intégrée
              </p>
            </div>
          </div>

          <div className="relative">
            <h1 className="mb-4 max-w-md text-4xl font-semibold leading-tight tracking-tight">
              Prêt à piloter votre établissement&nbsp;?
            </h1>
            <p className="max-w-md text-sm leading-relaxed text-[var(--color-ink-dim)]">
              Créez votre compte administrateur et commencez la gestion pédagogique,
              administrative et financière.
            </p>
          </div>

          <p className="relative text-xs text-[var(--color-ink-faint)]">
            © {new Date().getFullYear()} Collège Auréole — Tous droits réservés.
          </p>
        </section>

        {/* ── Form panel ─────────────────────────────────────────── */}
        <section className="flex items-center justify-center px-6 py-10 sm:px-10">
          <div className="w-full max-w-md">
            {/* Mobile logo */}
            <div className="mb-8 flex items-center gap-3 lg:hidden">
              <img
                src="/logo-aureole.jpeg"
                alt="Logo"
                className="h-10 w-10 rounded-lg object-cover ring-1 ring-[var(--color-border)]"
              />
              <div>
                <p className="text-base font-semibold text-[var(--color-halo)]">
                  Collège Auréole
                </p>
                <p className="text-xs text-[var(--color-ink-dim)]">
                  Système de Gestion Intégrée
                </p>
              </div>
            </div>

            {step === 'checking' && (
              <div className="flex items-center justify-center py-24">
                <Loader2 className="size-6 animate-spin text-[var(--color-brand)]" />
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

            {step === 'seeding' && (
              <div className="rounded-[var(--radius-lg)] border border-[var(--color-border)] bg-[var(--color-surface)] p-10 text-center shadow-[var(--shadow-soft)]">
                <StepIndicator current={activeStep} />
                <div className="relative mx-auto mb-6 h-20 w-20">
                  <span className="absolute inset-0 animate-ping rounded-full bg-[var(--color-brand)]/20" />
                  <span className="absolute inset-0 flex items-center justify-center rounded-full bg-[var(--color-brand-wash)]">
                    <Loader2 className="size-8 animate-spin text-[var(--color-brand)]" />
                  </span>
                </div>
                <h2 className="text-xl font-semibold text-[var(--color-ink)]">
                  Initialisation en cours
                </h2>
                <p className="mt-2 min-h-5 text-sm text-[var(--color-ink-dim)]">
                  {progress || 'Veuillez patienter, cela ne prend que quelques secondes...'}
                </p>
                <div className="mt-8 h-1.5 w-full overflow-hidden rounded-full bg-[var(--color-surface-3)]">
                  <div className="h-full w-1/3 animate-pulse rounded-full bg-gradient-to-r from-transparent via-[var(--color-brand)] to-transparent" />
                </div>
              </div>
            )}

            {step === 'form' && (
              <>
                <div className="rounded-[var(--radius-lg)] border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-[var(--shadow-soft)]">
                  <div className="mb-5 flex items-start justify-between">
                    <div>
                      <div className="mb-3 inline-flex h-9 w-9 items-center justify-center rounded-lg bg-[var(--color-brand-wash)] text-[var(--color-brand)]">
                        <GraduationCap className="h-4 w-4" />
                      </div>
                      <h2 className="text-2xl font-semibold tracking-tight text-[var(--color-ink)]">
                        Configuration initiale
                      </h2>
                      <p className="mt-1 text-sm text-[var(--color-ink-dim)]">
                        Créez le compte administrateur de l’établissement.
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

                  <form onSubmit={handleSubmit} className="flex flex-col gap-3" noValidate>
                    <div className="grid grid-cols-2 gap-3">
                      <Input
                        label="Nom"
                        type="text"
                        autoComplete="family-name"
                        value={nom}
                        onChange={(e) => setNom(e.target.value)}
                        required
                      />
                      <Input
                        label="Prénom"
                        type="text"
                        autoComplete="given-name"
                        value={prenom}
                        onChange={(e) => setPrenom(e.target.value)}
                        required
                      />
                    </div>

                    <Input
                      label="Adresse e-mail administrateur"
                      type="email"
                      autoComplete="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      hint="Cet e-mail sera utilisé pour vous connecter."
                      required
                    />

                    <div className="flex flex-col gap-1.5">
                      <label htmlFor="setup-password" className="text-sm font-medium text-[var(--color-ink-dim)]">
                        Mot de passe
                      </label>
                      <div className="relative">
                        <input
                          id="setup-password"
                          value={password}
                          onChange={(e) => setPassword(e.target.value)}
                          type={showPwd ? 'text' : 'password'}
                          autoComplete="new-password"
                          required
                          className="h-10 w-full rounded-[var(--radius-sm)] border border-[var(--color-border)] bg-[var(--color-surface-2)] px-3 pr-10 text-sm text-[var(--color-ink)] outline-none transition-colors duration-150 focus-visible:border-[var(--color-halo)] focus-visible:ring-2 focus-visible:ring-[var(--color-halo)]"
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
                    </div>

                    <label className="mt-1 flex cursor-pointer items-start gap-3 rounded-[var(--radius-sm)] border border-[var(--color-border)] bg-[var(--color-surface-2)] p-3 transition-all duration-150 hover:border-[var(--color-brand)]/50 hover:bg-[var(--color-surface-3)]">
                      <input
                        type="checkbox"
                        checked={seedData}
                        onChange={(e) => setSeedData(e.target.checked)}
                        className="mt-0.5 size-4 shrink-0 accent-[var(--color-brand)]"
                      />
                      <span>
                        <span className="block text-sm font-medium text-[var(--color-ink)]">
                          Données d’exemple
                        </span>
                        <span className="block text-xs text-[var(--color-ink-dim)]">
                          Élèves, enseignants, notes et paiements pour tester immédiatement.
                        </span>
                      </span>
                    </label>

                    {error && (
                      <p
                        role="alert"
                        className="rounded-[var(--radius-sm)] border border-[var(--color-danger)]/30 bg-[var(--color-danger-wash)] px-3 py-2 text-sm text-[var(--color-danger)]"
                      >
                        {error}
                      </p>
                    )}

                    <Button
                      type="submit"
                      variant="primary"
                      size="md"
                      disabled={!nom.trim() || !prenom.trim() || !email || !password}
                      className="mt-2 w-full"
                    >
                      Initialiser l’établissement
                      <ArrowRight className="size-4" />
                    </Button>
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
