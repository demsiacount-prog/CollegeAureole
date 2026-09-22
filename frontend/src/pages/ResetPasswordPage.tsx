import { useMemo, useState, type FormEvent } from 'react'
import { useSearchParams } from 'react-router-dom'
import { AlertCircle, KeyRound } from 'lucide-react'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { LogoEtablissement } from '@/components/ui/LogoEtablissement'
import { useEtablissement } from '@/features/etablissement/useEtablissement'
import { required, validateFields, hasErrors, type Errors } from '@/lib/validation'
import { api, extractErrorMessage } from '@/lib/api'

const MIN_LONGUEUR = 8

export function ResetPasswordPage() {
  const { data: etab } = useEtablissement()
  const [searchParams] = useSearchParams()
  const jeton = useMemo(() => searchParams.get('jeton') ?? '', [searchParams])
  const [motDePasse, setMotDePasse] = useState('')
  const [confirmation, setConfirmation] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [succes, setSucces] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [fieldErrors, setFieldErrors] = useState<Errors>({})

  const logo = etab?.logo
  const nom = etab?.nom ?? 'Gestion Scolaire'

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    const errs = validateFields({
      mot_de_passe: required(motDePasse, 'Le nouveau mot de passe') ?? (
        motDePasse.length < MIN_LONGUEUR
          ? `Le nouveau mot de passe doit contenir au moins ${MIN_LONGUEUR} caractères.`
          : undefined
      ),
      confirmation: required(confirmation, 'La confirmation'),
    })
    if (!errs.confirmation && confirmation !== motDePasse) {
      errs.confirmation = 'La confirmation ne correspond pas au nouveau mot de passe.'
    }
    setFieldErrors(errs)
    if (hasErrors(errs)) return
    setIsSubmitting(true)
    try {
      await api.post('/api/auth/reinitialiser-mot-de-passe', {
        jeton,
        nouveau_mot_de_passe: motDePasse,
      })
      setSucces('Mot de passe réinitialisé. Vous pouvez vous connecter avec votre nouveau mot de passe.')
    } catch (err) {
      setError(extractErrorMessage(err, "La réinitialisation du mot de passe a échoué."))
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
              Réinitialisation
            </h1>
            <p className="mt-1 text-sm text-[var(--ink-dim)]">
              Choisissez un nouveau mot de passe pour votre compte.
            </p>
          </div>

          {!jeton ? (
            <div className="flex flex-col gap-4">
              <p role="alert" className="rounded-[var(--radius-sm)] border border-[var(--danger)]/30 bg-[var(--danger-w)] px-3 py-2.5 text-sm text-[var(--danger)]">
                <AlertCircle className="mr-1.5 inline h-4 w-4" />
                Lien de réinitialisation invalide&nbsp;: le jeton est manquant.
              </p>
              <Button variant="secondary" size="md" to="/connexion" className="w-full">
                Retour à la connexion
              </Button>
            </div>
          ) : succes ? (
            <div className="flex flex-col gap-4">
              <p role="status" className="rounded-[var(--radius-sm)] border border-[var(--action)]/30 bg-[var(--action-w)] px-3 py-2.5 text-sm text-[var(--ink)]">
                {succes}
              </p>
              <Button variant="secondary" size="md" to="/connexion" className="w-full">
                Aller à la connexion
              </Button>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="flex flex-col gap-4" noValidate>
              <Input
                label="Nouveau mot de passe"
                type="password"
                autoComplete="new-password"
                value={motDePasse}
                onChange={(e) => {
                  setMotDePasse(e.target.value)
                  if (fieldErrors.mot_de_passe) setFieldErrors((p) => ({ ...p, mot_de_passe: undefined }))
                }}
                placeholder="••••••••"
                required
                hint={`Au moins ${MIN_LONGUEUR} caractères.`}
                error={fieldErrors.mot_de_passe}
              />
              <Input
                label="Confirmer le mot de passe"
                type="password"
                autoComplete="new-password"
                value={confirmation}
                onChange={(e) => {
                  setConfirmation(e.target.value)
                  if (fieldErrors.confirmation) setFieldErrors((p) => ({ ...p, confirmation: undefined }))
                }}
                placeholder="••••••••"
                required
                error={fieldErrors.confirmation}
              />

              {error && (
                <p role="alert" className="rounded-[var(--radius-sm)] border border-[var(--danger)]/30 bg-[var(--danger-w)] px-3 py-2 text-sm text-[var(--danger)]">
                  {error}
                </p>
              )}

              <Button type="submit" variant="primary" size="md" isLoading={isSubmitting} className="mt-2 w-full">
                Enregistrer le nouveau mot de passe
              </Button>
            </form>
          )}
        </div>
      </div>
    </div>
  )
}