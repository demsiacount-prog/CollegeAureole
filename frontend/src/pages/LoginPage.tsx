import { useState, type FormEvent } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { Eye, EyeOff, LockKeyhole, Moon, Sun } from 'lucide-react'
import { clsx } from 'clsx'
import { useAuth } from '@/auth/useAuth'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { LogoEtablissement } from '@/components/ui/LogoEtablissement'
import { useTheme } from '@/hooks/useTheme'
import { useEtablissement } from '@/features/etablissement/useEtablissement'
import { required, email as emailVal, validateFields, hasErrors, type Errors } from '@/lib/validation'

export function LoginPage() {
  const { login, isAuthenticated } = useAuth()
  const { theme, toggle: toggleTheme } = useTheme()
  const { data: etab } = useEtablissement()
  const navigate = useNavigate()
  const location = useLocation()
  const [email, setEmail] = useState('')
  const [motDePasse, setMotDePasse] = useState('')
  const [showPwd, setShowPwd] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [fieldErrors, setFieldErrors] = useState<Errors>({})
 

  const logo = etab?.logo
  const nom = etab?.nom ?? 'Gestion Scolaire'
  const sigle = etab?.sigle?.trim() ? ` (${etab.sigle.trim()})` : ''

  if (isAuthenticated) {
    const from = (location.state as { from?: Location })?.from?.pathname ?? '/app'
    return <Navigate to={from} replace />
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    const errs = validateFields({
      email: required(email, 'Adresse e-mail') ?? emailVal(email),
      mot_de_passe: required(motDePasse, 'Mot de passe'),
    })
    setFieldErrors(errs)
    if (hasErrors(errs)) return
    setIsSubmitting(true)
    try {
      await login(email, motDePasse)
      navigate('/app', { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Connexion impossible.')
    } finally {
      setIsSubmitting(false)
    }
  }


  return (
    <div className="min-h-screen bg-[var(--color-base)] px-6 py-8 text-[var(--color-ink)]">
      <div className="mx-auto flex min-h-[calc(100vh-4rem)] max-w-6xl items-center gap-12">
        {/* Left brand panel */}
        <section className="hidden flex-1 lg:block">
          <div className="mb-8 flex items-center gap-3">
            <LogoEtablissement
              src={logo}
              nom={nom}
              label
              className="h-14 w-14 rounded-lg bg-[var(--color-surface-2)] p-1 ring-1 ring-[var(--color-border)]"
            />
            <div>
              <p className="font-[var(--font-display)] text-xl font-semibold text-[var(--color-halo)]">
                {nom}
                {sigle}
              </p>
              <p className="text-xs text-[var(--color-ink-dim)]">
                Système de Gestion Intégrée
              </p>
            </div>
          </div>

          <h1 className="mb-8 max-w-lg font-[var(--font-display)] text-3xl font-semibold leading-tight text-[var(--color-ink)]">
            Accès sécurisé à la gestion pédagogique, administrative et financière.
          </h1>
        </section>

        {/* Right form panel */}
        <section className="mx-auto w-full max-w-md">
          {/* Mobile logo */}
          <div className="mb-8 flex items-center gap-3 lg:hidden">
            <LogoEtablissement
              src={logo}
              nom={nom}
              className="h-11 w-11 rounded-lg bg-[var(--color-surface-2)] p-1 ring-1 ring-[var(--color-border)]"
            />
            <div>
              <p className="font-[var(--font-display)] text-base font-semibold text-[var(--color-halo)]">
                {nom}
                {sigle}
              </p>
              <p className="text-xs text-[var(--color-ink-dim)]">
                Système de Gestion Intégrée
              </p>
            </div>
          </div>

          {/* Card */}
          <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-[var(--shadow-soft)]">
            {/* Card header with theme toggle */}
            <div className="mb-6 flex items-start justify-between">
              <div>
                <div className="mb-3 inline-flex h-10 w-10 items-center justify-center rounded-lg bg-[var(--color-action)] text-white">
                  <LockKeyhole className="h-5 w-5" />
                </div>
                <h2 className="font-[var(--font-display)] text-2xl font-semibold tracking-tight text-[var(--color-ink)]">
                  Connexion
                </h2>
                <p className="mt-1 text-sm text-[var(--color-ink-dim)]">
                  Accédez à votre espace de gestion.
                </p>
              </div>
              <button
                type="button"
                onClick={toggleTheme}
                className="rounded-md border border-[var(--color-border)] p-2 text-[var(--color-ink-dim)] hover:bg-[var(--color-surface-2)] transition-colors"
              >
                {theme === 'dark' ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
              </button>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit} className="flex flex-col gap-4" noValidate>
              <Input
                label="Adresse e-mail"
                type="email"
                autoComplete="email"
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value)
                  if (fieldErrors.email) setFieldErrors((p) => ({ ...p, email: undefined }))
                }}
                placeholder="prenom.nom@etablissement.com"
                required
                error={fieldErrors.email}
              />

              {/* Password field with visibility toggle */}
              <div className="flex flex-col gap-1.5">
                <label className="text-sm font-medium text-[var(--color-ink-dim)]">
                  Mot de passe
                </label>
                <div className="relative">
                  <input
                    value={motDePasse}
                    onChange={(e) => {
                      setMotDePasse(e.target.value)
                      if (fieldErrors.mot_de_passe) setFieldErrors((p) => ({ ...p, mot_de_passe: undefined }))
                    }}
                    type={showPwd ? 'text' : 'password'}
                    autoComplete="current-password"
                    placeholder="••••••••"
                    required
                    className={clsx(
                      'h-10 w-full rounded-[var(--radius-sm)] border bg-[var(--color-surface-2)] px-3 pr-10 text-sm text-[var(--color-ink)] placeholder:text-[var(--color-ink-faint)] outline-none transition-colors duration-150 focus-visible:border-[var(--color-halo)] focus-visible:ring-2 focus-visible:ring-[var(--color-halo)]',
                      fieldErrors.mot_de_passe ? 'border-[var(--color-danger)]' : 'border-[var(--color-border)]',
                    )}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPwd((v) => !v)}
                    className="absolute right-2 top-1/2 -translate-y-1/2 rounded-md p-1 text-[var(--color-ink-dim)] hover:bg-[var(--color-surface-3)] transition-colors"
                  >
                    {showPwd ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
                {fieldErrors.mot_de_passe && (
                  <p className="text-xs text-[var(--color-danger)]">{fieldErrors.mot_de_passe}</p>
                )}
              </div>

              {error && (
                <p role="alert" className="rounded-[var(--radius-sm)] border border-[var(--color-danger)]/30 bg-[var(--color-danger-wash)] px-3 py-2 text-sm text-[var(--color-danger)]">
                  {error}
                </p>
              )}

              <Button type="submit" variant="primary" size="md" isLoading={isSubmitting} className="mt-2 w-full">
                Se connecter
              </Button>
            </form>
          </div>

          <p className="mt-8 text-center text-xs text-[var(--color-ink-faint)]">
            Accès réservé au personnel administratif de l'établissement.
          </p>
         
        </section>
      </div>
    </div>
  )
}
