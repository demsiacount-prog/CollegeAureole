import { useState } from 'react'
import { Drawer } from '@/components/ui/Drawer'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { required, minLength, validateFields, hasErrors, type Errors } from '@/lib/validation'
import type { Utilisateur } from './types'

interface Props {
  utilisateur: Utilisateur | null
  onClose: () => void
  onSubmit: (nouveau_mot_de_passe: string) => void
}

export default function ReinitialiserMotDePasseDrawer({ utilisateur, onClose, onSubmit }: Props) {
  const [motDePasse, setMotDePasse] = useState('')
  const [confirmation, setConfirmation] = useState('')
  const [errors, setErrors] = useState<Errors>({})

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const mdpErr = required(motDePasse, 'Le nouveau mot de passe') ?? minLength(motDePasse, 8, 'Le nouveau mot de passe')
    let confirmErr = required(confirmation, 'La confirmation')
    if (!mdpErr && motDePasse !== confirmation) {
      confirmErr = 'Les deux mots de passe ne correspondent pas.'
    }
    const errs = validateFields({ mot_de_passe: mdpErr, confirmation: confirmErr })
    setErrors(errs)
    if (hasErrors(errs)) return
    onSubmit(motDePasse)
    setMotDePasse('')
    setConfirmation('')
    setErrors({})
  }

  return (
    <Drawer
      open={!!utilisateur}
      onClose={onClose}
      title={utilisateur ? `Réinitialiser le mot de passe — ${utilisateur.prenom} ${utilisateur.nom}` : ''}
    >
      <form onSubmit={handleSubmit} noValidate className="flex h-full flex-col">
        <div className="flex-1 space-y-4 overflow-y-auto p-6">
          <Input
            label="Nouveau mot de passe"
            type="password"
            value={motDePasse}
            onChange={(e) => {
              setMotDePasse(e.target.value)
              if (errors.mot_de_passe) setErrors((prev) => ({ ...prev, mot_de_passe: undefined }))
            }}
            placeholder="Au moins 8 caractères"
            required
            error={errors.mot_de_passe}
          />
          <Input
            label="Confirmer le nouveau mot de passe"
            type="password"
            value={confirmation}
            onChange={(e) => {
              setConfirmation(e.target.value)
              if (errors.confirmation) setErrors((prev) => ({ ...prev, confirmation: undefined }))
            }}
            placeholder="••••••••"
            required
            error={errors.confirmation}
          />
        </div>

        <div className="border-t border-[var(--color-border)] p-4">
          <Button type="submit" variant="primary" className="w-full">
            Réinitialiser le mot de passe
          </Button>
        </div>
      </form>
    </Drawer>
  )
}