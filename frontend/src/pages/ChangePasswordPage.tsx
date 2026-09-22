import { useState, type FormEvent } from 'react'
import { KeyRound } from 'lucide-react'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { PageHeader } from '@/components/ui/PageHeader'
import { toast } from '@/components/ui/toast'
import { useAuth } from '@/auth/useAuth'
import { required, validateFields, hasErrors, type Errors } from '@/lib/validation'
import { api, extractErrorMessage } from '@/lib/api'

const MIN_LONGUEUR = 8

export function ChangePasswordPage() {
  const { user } = useAuth()
  const [ancien, setAncien] = useState('')
  const [nouveau, setNouveau] = useState('')
  const [confirmation, setConfirmation] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [fieldErrors, setFieldErrors] = useState<Errors>({})

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    const errs = validateFields({
      ancien: required(ancien, "L'ancien mot de passe"),
      nouveau: required(nouveau, 'Le nouveau mot de passe') ?? (
        nouveau.length < MIN_LONGUEUR
          ? `Le nouveau mot de passe doit contenir au moins ${MIN_LONGUEUR} caractères.`
          : undefined
      ),
      confirmation: required(confirmation, 'La confirmation'),
    })
    if (!errs.confirmation && confirmation !== nouveau) {
      errs.confirmation = 'La confirmation ne correspond pas au nouveau mot de passe.'
    }
    if (nouveau && nouveau === ancien) {
      errs.nouveau = 'Le nouveau mot de passe doit être différent de l\'ancien.'
    }
    setFieldErrors(errs)
    if (hasErrors(errs)) return
    if (!user) return
    setIsSubmitting(true)
    try {
      await api.put(`/api/auth/utilisateurs/${user.id}/mot-de-passe`, {
        ancien_mot_de_passe: ancien,
        nouveau_mot_de_passe: nouveau,
      })
      setAncien('')
      setNouveau('')
      setConfirmation('')
      toast('Mot de passe modifié avec succès.', 'success')
    } catch (err) {
      setError(extractErrorMessage(err, 'La modification du mot de passe a échoué.'))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="flex flex-col gap-5">
      <PageHeader
        title="Mon mot de passe"
        eyebrow="Compte"
        subtitle="Modifiez le mot de passe de votre compte."
      />

      <div className="mx-auto w-full max-w-md">
        <div className="rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--surface)] p-6 shadow-[var(--shadow-card)]">
          <div className="mb-6 flex items-start gap-3">
            <div className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-[var(--radius-md)] bg-[var(--action)] text-white">
              <KeyRound className="h-5 w-5" />
            </div>
            <div>
              <h2 className="font-[var(--font-serif)] text-xl font-semibold tracking-tight">Changer mon mot de passe</h2>
              <p className="mt-1 text-sm text-[var(--ink-dim)]">
                L'ancien mot de passe est requis pour confirmer la modification.
              </p>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="flex flex-col gap-4" noValidate>
            <Input
              label="Ancien mot de passe"
              type="password"
              autoComplete="current-password"
              value={ancien}
              onChange={(e) => {
                setAncien(e.target.value)
                if (fieldErrors.ancien) setFieldErrors((p) => ({ ...p, ancien: undefined }))
              }}
              placeholder="••••••••"
              required
              error={fieldErrors.ancien}
            />
            <Input
              label="Nouveau mot de passe"
              type="password"
              autoComplete="new-password"
              value={nouveau}
              onChange={(e) => {
                setNouveau(e.target.value)
                if (fieldErrors.nouveau) setFieldErrors((p) => ({ ...p, nouveau: undefined }))
              }}
              placeholder="••••••••"
              required
              hint={`Au moins ${MIN_LONGUEUR} caractères, différent de l'ancien.`}
              error={fieldErrors.nouveau}
            />
            <Input
              label="Confirmer le nouveau mot de passe"
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
              Enregistrer
            </Button>
          </form>
        </div>
      </div>
    </div>
  )
}