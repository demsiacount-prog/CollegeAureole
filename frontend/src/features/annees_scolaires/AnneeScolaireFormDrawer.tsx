import { useState } from 'react'
import { Drawer } from '@/components/ui/Drawer'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { required, dateFinApresDebut, validateFields, hasErrors, type Errors } from '@/lib/validation'
import type { AnneeScolaireCreateInput } from './types'

interface Props {
  open: boolean
  onClose: () => void
  onSubmit: (data: AnneeScolaireCreateInput) => void
}

export default function AnneeScolaireFormDrawer({ open, onClose, onSubmit }: Props) {
  const [libelle, setLibelle] = useState('')
  const [dateDebut, setDateDebut] = useState('')
  const [dateFin, setDateFin] = useState('')
  const [errors, setErrors] = useState<Errors>({})

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const errs = validateFields({
      libelle: required(libelle, 'Le libellé'),
      date_debut: required(dateDebut, 'La date de début'),
      date_fin: required(dateFin, 'La date de fin') ?? dateFinApresDebut(dateDebut, dateFin),
    })
    setErrors(errs)
    if (hasErrors(errs)) return
    onSubmit({
      libelle,
      date_debut: dateDebut,
      date_fin: dateFin,
    })
    setLibelle('')
    setDateDebut('')
    setDateFin('')
    setErrors({})
  }

  return (
    <Drawer open={open} onClose={onClose} title="Nouvelle année scolaire">
      <form onSubmit={handleSubmit} noValidate className="flex flex-col h-full">
        <div className="flex-1 overflow-y-auto space-y-4">
          <Input
            label="Libellé"
            value={libelle}
            onChange={(e) => {
              setLibelle(e.target.value)
              if (errors.libelle) setErrors((prev) => ({ ...prev, libelle: undefined }))
            }}
            placeholder="ex. 2025-2026"
            required
            error={errors.libelle}
          />
          <Input
            label="Date de début"
            type="date"
            value={dateDebut}
            onChange={(e) => {
              setDateDebut(e.target.value)
              if (errors.date_debut) setErrors((prev) => ({ ...prev, date_debut: undefined, date_fin: undefined }))
            }}
            required
            error={errors.date_debut}
          />
          <Input
            label="Date de fin"
            type="date"
            value={dateFin}
            onChange={(e) => {
              setDateFin(e.target.value)
              if (errors.date_fin) setErrors((prev) => ({ ...prev, date_fin: undefined }))
            }}
            required
            error={errors.date_fin}
          />
        </div>

        <div className="p-4 border-t border-[var(--color-border)]">
          <Button type="submit" variant="primary" className="w-full">
            Créer
          </Button>
        </div>
      </form>
    </Drawer>
  )
}
