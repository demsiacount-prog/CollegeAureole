import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Drawer } from '@/components/ui/Drawer'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { SearchableSelect } from '@/components/ui/SearchableSelect'
import { fetchEleves } from '@/features/eleves/api'
import { fetchCours } from '@/features/cours/api'
import { required, validateFields, hasErrors, type Errors } from '@/lib/validation'
import type { AbsenceCreateInput } from './types'

interface Props {
  open: boolean
  onClose: () => void
  onSubmit: (data: AbsenceCreateInput) => void
}

export default function AbsenceFormDrawer({ open, onClose, onSubmit }: Props) {
  const { data: eleves = [] } = useQuery({ queryKey: ['eleves', 'select'], queryFn: () => fetchEleves({ limit: 5000 }) })
  const { data: cours = [] } = useQuery({ queryKey: ['cours'], queryFn: fetchCours })

  const [matriculeEleve, setMatriculeEleve] = useState('')
  const [idCours, setIdCours] = useState('')
  const [dateAbsence, setDateAbsence] = useState(new Date().toISOString().split('T')[0])
  const [motif, setMotif] = useState('')
  const [errors, setErrors] = useState<Errors>({})

  const eleve = eleves.find((el) => el.matricule === matriculeEleve) ?? null
  const classeId = eleve?.classe?.id ?? null
  const coursClasse = classeId
    ? cours.filter((c) => c.classes.some((cl) => cl.id === classeId))
    : []

  const handleEleveChange = (value: string) => {
    setMatriculeEleve(value)
    setIdCours('')
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const errs = validateFields({
      matricule_eleve: required(matriculeEleve, "L'élève"),
      date_absence: required(dateAbsence, "La date d'absence"),
    })
    setErrors(errs)
    if (hasErrors(errs)) return
    onSubmit({
      matricule_eleve: matriculeEleve,
      id_cours: idCours ? Number(idCours) : null,
      date_absence: dateAbsence,
      motif: motif || null,
    })
    setMatriculeEleve('')
    setIdCours('')
    setDateAbsence(new Date().toISOString().split('T')[0])
    setMotif('')
    setErrors({})
  }

  return (
    <Drawer open={open} onClose={onClose} title="Enregistrer une absence">
      <form onSubmit={handleSubmit} noValidate className="flex flex-col h-full">
        <div className="flex-1 overflow-y-auto space-y-4">
          <SearchableSelect
            label="Élève"
            value={matriculeEleve}
            onChange={(v) => {
              handleEleveChange(v)
              if (errors.matricule_eleve) setErrors((prev) => ({ ...prev, matricule_eleve: undefined }))
            }}
            options={eleves.map((el) => ({
              value: el.matricule,
              label: `${el.prenom} ${el.nom}`.trim(),
              sublabel: el.matricule,
            }))}
            placeholder="Rechercher un élève…"
            emptyMessage="Aucun élève trouvé"
            error={errors.matricule_eleve}
          />

          <Select
            label="Cours (optionnel)"
            value={idCours}
            onChange={(e) => setIdCours(e.target.value)}
            disabled={!eleve || !classeId}
          >
            <option value="">
              {!eleve
                ? 'Sélectionnez d’abord un élève'
                : classeId
                  ? '— Aucun —'
                  : 'Élève sans classe pour l’année active'}
            </option>
            {coursClasse.map((c) => (
              <option key={c.id} value={c.id}>{c.nom}</option>
            ))}
          </Select>

          <Input label="Date d'absence" type="date" value={dateAbsence} onChange={(e) => { setDateAbsence(e.target.value); if (errors.date_absence) setErrors((prev) => ({ ...prev, date_absence: undefined })) }} max={new Date().toISOString().split('T')[0]} required error={errors.date_absence} />
          <Input label="Motif (optionnel)" placeholder="ex. Maladie" value={motif} onChange={(e) => setMotif(e.target.value)} />
        </div>

        <div className="pt-4 mt-2 border-t border-[var(--color-border)]">
          <Button type="submit" variant="primary" className="w-full">
            Enregistrer
          </Button>
        </div>
      </form>
    </Drawer>
  )
}
