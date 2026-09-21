import { useState } from 'react'
import { Drawer } from '@/components/ui/Drawer'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { required, email, minLength, validateFields, hasErrors, type Errors } from '@/lib/validation'
import { ROLE_OPTIONS, type UtilisateurCreateInput } from './types'

interface Props {
  open: boolean
  onClose: () => void
  onSubmit: (data: UtilisateurCreateInput) => void
}

export default function UtilisateurFormDrawer({ open, onClose, onSubmit }: Props) {
  const [prenom, setPrenom] = useState('')
  const [nom, setNom] = useState('')
  const [emailValue, setEmailValue] = useState('')
  const [role, setRole] = useState('ADMIN')
  const [motDePasse, setMotDePasse] = useState('')
  const [errors, setErrors] = useState<Errors>({})

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const errs = validateFields({
      prenom: required(prenom, 'Le prénom'),
      nom: required(nom, 'Le nom'),
      email: required(emailValue, 'L’e-mail') ?? email(emailValue),
      mot_de_passe: required(motDePasse, 'Le mot de passe') ?? minLength(motDePasse, 8, 'Le mot de passe'),
    })
    setErrors(errs)
    if (hasErrors(errs)) return
    onSubmit({ prenom, nom, email: emailValue, mot_de_passe: motDePasse, role })
    setPrenom('')
    setNom('')
    setEmailValue('')
    setRole('ADMIN')
    setMotDePasse('')
    setErrors({})
  }

  return (
    <Drawer open={open} onClose={onClose} title="Nouvel utilisateur">
      <form onSubmit={handleSubmit} noValidate className="flex h-full flex-col">
        <div className="flex-1 space-y-4 overflow-y-auto p-6">
          <Input
            label="Prénom"
            value={prenom}
            onChange={(e) => {
              setPrenom(e.target.value)
              if (errors.prenom) setErrors((prev) => ({ ...prev, prenom: undefined }))
            }}
            placeholder="ex. Aminata"
            required
            error={errors.prenom}
          />
          <Input
            label="Nom"
            value={nom}
            onChange={(e) => {
              setNom(e.target.value)
              if (errors.nom) setErrors((prev) => ({ ...prev, nom: undefined }))
            }}
            placeholder="ex. Traoré"
            required
            error={errors.nom}
          />
          <Input
            label="E-mail"
            type="email"
            value={emailValue}
            onChange={(e) => {
              setEmailValue(e.target.value)
              if (errors.email) setErrors((prev) => ({ ...prev, email: undefined }))
            }}
            placeholder="ex. aminata@ecole.ml"
            required
            error={errors.email}
          />
          <Select
            label="Rôle"
            value={role}
            onChange={(e) => setRole(e.target.value)}
            options={ROLE_OPTIONS}
          />
          <Input
            label="Mot de passe"
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
        </div>

        <div className="border-t border-[var(--border)] p-4">
          <Button type="submit" variant="primary" className="w-full">
            Créer l'utilisateur
          </Button>
        </div>
      </form>
    </Drawer>
  )
}