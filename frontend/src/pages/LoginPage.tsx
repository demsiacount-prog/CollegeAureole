import { useState, type FormEvent } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '@/auth/AuthContext'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'

export function LoginPage() {
  const { login, isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [email, setEmail] = useState('')
  const [motDePasse, setMotDePasse] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  if (isAuthenticated) {
    const from = (location.state as { from?: Location })?.from?.pathname ?? '/app'
    return <Navigate to={from} replace />
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
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
    <div className="flex min-h-screen w-full bg-[var(--color-base)]">
      {/* Panneau de marque — visible dès lg, porte le vrai logo et la devise */}
      <div className="relative hidden w-1/2 overflow-hidden border-r border-[var(--color-border-soft)] lg:flex lg:flex-col lg:justify-between">
        <div className="pointer-events-none absolute -left-32 top-1/4 size-[520px] rounded-full bg-[var(--color-halo)] opacity-[0.12] blur-[130px]" />
        <div className="pointer-events-none absolute -right-20 bottom-0 size-[420px] rounded-full bg-[var(--color-brand-blue)] opacity-[0.14] blur-[130px]" />
        <div className="pointer-events-none absolute left-1/4 top-1/5 size-64 rounded-full border border-[var(--color-halo-dim)] opacity-30" />

        <div className="relative z-10 px-14 pt-14">
          <img src="/logo-mark.png" alt="Collège Auréole" className="h-32 w-auto object-contain" />
        </div>

        <div className="relative z-10 px-14 pb-16">
          <p className="mb-4 font-[var(--font-display)] italic text-[26px] leading-snug tracking-tight text-[var(--color-halo-bright)]">
            « L’excellent n’a pas de concurrent »
          </p>
          <p className="max-w-sm text-[15px] leading-relaxed text-[var(--color-ink-dim)]">
            Dossiers, notes, absences, finances : un seul espace pour piloter
            l’établissement, du secrétariat à la direction.
          </p>
        </div>
      </div>

      {/* Formulaire */}
      <div className="flex w-full flex-1 flex-col items-center justify-center px-6 py-12">
        <div className="w-full max-w-sm">
          <div className="mb-8 lg:hidden">
            <img src="/logo-emblem.png" alt="Collège Auréole" className="h-16 w-auto object-contain" />
          </div>

          <h1 className="mb-1 font-[var(--font-display)] text-[26px] font-medium tracking-tight text-[var(--color-ink)]">
            Connexion
          </h1>
          <p className="mb-8 text-sm text-[var(--color-ink-dim)]">
            Accédez à votre espace de gestion.
          </p>

          <form onSubmit={handleSubmit} className="flex flex-col gap-4" noValidate>
            <Input
              label="Adresse e-mail"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="prenom.nom@aureole.ma"
              required
            />
            <Input
              label="Mot de passe"
              type="password"
              autoComplete="current-password"
              value={motDePasse}
              onChange={(e) => setMotDePasse(e.target.value)}
              placeholder="••••••••"
              required
            />

            {error && (
              <p role="alert" className="rounded-[var(--radius-sm)] border border-[var(--color-danger)]/30 bg-[var(--color-danger-wash)] px-3 py-2 text-sm text-[var(--color-danger)]">
                {error}
              </p>
            )}

            <Button type="submit" variant="primary" size="md" isLoading={isSubmitting} className="mt-2 w-full">
              Se connecter
            </Button>
          </form>

          <p className="mt-8 text-center text-xs text-[var(--color-ink-faint)]">
            Accès réservé au personnel administratif de l’établissement.
          </p>
        </div>
      </div>
    </div>
  )
}
