import { useState, type FormEvent } from 'react'
import { ArrowLeft, KeyRound } from 'lucide-react'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { LogoEtablissement } from '@/components/ui/LogoEtablissement'
import { useEtablissement } from '@/features/etablissement/useEtablissement'
import { required, email as emailVal, validateFields, hasErrors, type Errors } from '@/lib/validation'
import { api, extractErrorMessage } from '@/lib/api'

export function ForgotPasswordPage() {
  const { data: etab } = useEtablissement()
  const [email, setEmail] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [info, setInfo] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [fieldErrors, setFieldErrors] = useState<Errors>({})

  const logo = etab?.logo
  const nom = etab?.nom ?? 'Gestion Scolaire'

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    const errs = validateFields({
      email: required(email, 'Adresse e-mail') ?? emailVal(email),
    })
    setFieldErrors(errs)
    if (hasErrors(errs)) return
    setIsSubmitting(true)
    try {
      const res = await api.post('/api/auth/mot-de-passe-oublie', { email })
      setInfo((res.data as { message?: string }).message ?? 'La demande a été prise en compte.')
    } catch (err) {
      setError(extractErrorMessage(err, 'La demande de réinitialisation a échoué.'))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-[var(--base)] px-6 py-10 text-[var(--ink)]">
      <div className="w-full max-w-md">
        <div className="mb-8 flex items-center justify-center gap-3">
          <LogoEtablissement
            src={logo}
            nom={nom}
            label
            className="h-12 w-12 rounded-[var(--radius-md)] bg-[var(--surface-2)] p-1 ring-1 ring-[var(--border)]"
          />
          <p className="font-[var(--font-serif)] text-lg font-semibold text-[var(--halo)]">{nom}</p>
        </div>

        <div className="rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--surface)] p-6 shadow-[var(--shadow-card)]">
          <div className="mb-6">
            <div className="mb-3 inline-flex h-10 w-10 items-center justify-center rounded-[var(--radius-md)] bg-[var(--action)] text-white">
              <KeyRound className="h-5 w-5" />
            </div>
            <h1 className="font-[var(--font-serif)] text-2xl font-semibold tracking-tight">
              Mot de passe oublié&nbsp;?
            </h1>
            <p className="mt-1 text-sm text-[var(--ink-dim)]">
              Saisissez l'adresse e-mail de votre compte&nbsp;: un lien de réinitialisation pourra vous
              être envoyé.
            </p>
          </div>

          {info ? (
            <div className="flex flex-col gap-4">
              <p
                role="status"
                className="rounded-[var(--radius-sm)] border border-[var(--action)]/30 bg-[var(--action-w)] px-3 py-2.5 text-sm text-[var(--ink)]"
              >
                {info}
              </p>
              <Button variant="secondary" size="md" to="/connexion" className="mt-2 w-full">
                <ArrowLeft className="h-4 w-4" />
                Retour à la connexion
              </Button>
            </div>
          ) : (
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

              {error && (
                <p role="alert" className="rounded-[var(--radius-sm)] border border-[var(--danger)]/30 bg-[var(--danger-w)] px-3 py-2 text-sm text-[var(--danger)]">
                  {error}
                </p>
              )}

              <Button type="submit" variant="primary" size="md" isLoading={isSubmitting} className="mt-2 w-full">
                Envoyer le lien
              </Button>

              <Button variant="ghost" size="md" to="/connexion" className="w-full">
                <ArrowLeft className="h-4 w-4" />
                Retour à la connexion
              </Button>
            </form>
          )}
        </div>
      </div>
    </div>
  )
}