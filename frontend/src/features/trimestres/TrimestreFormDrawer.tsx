import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Drawer } from '@/components/ui/Drawer'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { fetchAnneesScolaires } from '@/features/annees_scolaires/api'
import { required, dateFinApresDebut, validateFields, hasErrors, type Errors } from '@/lib/validation'
import { TYPE_PERIODE_OPTIONS, type TypePeriode } from './types'
import type { TrimestreCreateInput } from './types'

interface Props {
  open: boolean
  onClose: () => void
  onSubmit: (data: TrimestreCreateInput) => void
}

export default function TrimestreFormDrawer({ open, onClose, onSubmit }: Props) {
  const { data: annees = [] } = useQuery({ queryKey: ['annees-scolaires'], queryFn: fetchAnneesScolaires })

  const [nom, setNom] = useState('')
  const [type, setType] = useState<TypePeriode>('TRIMESTRE')
  const [dateDebut, setDateDebut] = useState('')
  const [dateFin, setDateFin] = useState('')
  const [anneeScolaireId, setAnneeScolaireId] = useState('')
  const [errors, setErrors] = useState<Errors>({})

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const errs = validateFields({
      nom: required(nom, 'Le nom'),
      date_debut: required(dateDebut, 'La date de début'),
      date_fin: required(dateFin, 'La date de fin') ?? dateFinApresDebut(dateDebut, dateFin),
      annee_scolaire_id: required(anneeScolaireId, "L'année scolaire"),
    })
    setErrors(errs)
    if (hasErrors(errs)) return
    onSubmit({
      nom,
      type,
      date_debut: dateDebut,
      date_fin: dateFin,
      annee_scolaire_id: Number(anneeScolaireId),
    })
    setNom('')
    setType('TRIMESTRE')
    setDateDebut('')
    setDateFin('')
    setAnneeScolaireId('')
    setErrors({})
  }

  return (
    <Drawer open={open} onClose={onClose} title={type === 'COMPOSITION' ? 'Nouvelle composition' : 'Nouveau trimestre'}>
      <form onSubmit={handleSubmit} noValidate className="flex flex-col h-full">
        <div className="flex-1 overflow-y-auto space-y-4">
          <Select label="Type de période" value={type} onChange={(e) => setType(e.target.value as TypePeriode)}>
            {TYPE_PERIODE_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </Select>

          <Input
            label="Nom"
            value={nom}
            onChange={(e) => {
              setNom(e.target.value)
              if (errors.nom) setErrors((prev) => ({ ...prev, nom: undefined }))
            }}
            placeholder={type === 'COMPOSITION' ? 'ex. Composition 1' : 'ex. Trimestre 1'}
            required
            error={errors.nom}
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

          <Select label="Année scolaire" value={anneeScolaireId} onChange={(e) => { setAnneeScolaireId(e.target.value); if (errors.annee_scolaire_id) setErrors((prev) => ({ ...prev, annee_scolaire_id: undefined })) }} required error={errors.annee_scolaire_id}>
            <option value="">— Sélectionner —</option>
            {annees.map((a) => (
              <option key={a.id} value={a.id}>{a.libelle}</option>
            ))}
          </Select>
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
