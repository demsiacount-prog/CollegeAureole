import { useEffect, useState } from 'react'
import { Drawer } from '@/components/ui/Drawer'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { required, minNumber, validateFields, hasErrors, type Errors } from '@/lib/validation'
import type { Salle, SalleCreateInput } from './types'

interface Props {
  salle?: Salle | null
  open: boolean
  onClose: () => void
  onSubmit: (data: SalleCreateInput) => void
}

export default function SalleFormDrawer({ salle, open, onClose, onSubmit }: Props) {
  const isEdit = !!salle

  const [nom, setNom] = useState(salle?.nom ?? '')
  const [capacite, setCapacite] = useState(salle?.capacite != null ? String(salle.capacite) : '')
  const [errors, setErrors] = useState<Errors>({})

  // Réinitialise le formulaire à chaque ouverture (sinon valeurs fantômes
  // de l'édition précédente quand on repasse en création).
  useEffect(() => {
    if (open) {
      setNom(salle?.nom ?? '')
      setCapacite(salle?.capacite != null ? String(salle.capacite) : '')
      setErrors({})
    }
  }, [open, salle])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const errs = validateFields({
      nom: required(nom, 'Le nom'),
      capacite: capacite ? minNumber(capacite, 1, 'La capacité') : undefined,
    })
    setErrors(errs)
    if (hasErrors(errs)) return
    onSubmit({
      nom,
      capacite: capacite ? Number(capacite) : null,
    })
  }

  return (
    <Drawer open={open} onClose={onClose} title={isEdit ? 'Modifier la salle' : 'Nouvelle salle'}>
      <form onSubmit={handleSubmit} noValidate className="flex flex-col h-full">
        <div className="flex-1 overflow-y-auto space-y-4">
          <Input
            label="Nom"
            placeholder="ex. Salle 12"
            value={nom}
            onChange={(e) => {
              setNom(e.target.value)
              if (errors.nom) setErrors((prev) => ({ ...prev, nom: undefined }))
            }}
            required
            error={errors.nom}
          />
          <Input
            label="Capacité"
            type="number"
            placeholder="ex. 45"
            value={capacite}
            onChange={(e) => {
              setCapacite(e.target.value)
              if (errors.capacite) setErrors((prev) => ({ ...prev, capacite: undefined }))
            }}
            error={errors.capacite}
          />
        </div>

        <div className="p-4 border-t border-[var(--color-border)]">
          <Button type="submit" variant="primary" className="w-full">
            {isEdit ? 'Mettre à jour' : 'Créer'}
          </Button>
        </div>
      </form>
    </Drawer>
  )
}
