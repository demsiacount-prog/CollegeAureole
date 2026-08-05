import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Drawer } from '@/components/ui/Drawer'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { SearchableSelect } from '@/components/ui/SearchableSelect'
import { fetchEleves } from '@/features/eleves/api'
import { fetchCours } from '@/features/cours/api'
import type { AbsenceCreateInput } from './types'

interface Props {
  open: boolean
  onClose: () => void
  onSubmit: (data: AbsenceCreateInput) => void
}

export default function AbsenceFormDrawer({ open, onClose, onSubmit }: Props) {
  const { data: eleves = [] } = useQuery({ queryKey: ['eleves', 'select'], queryFn: () => fetchEleves({ limit: 500 }) })
  const { data: cours = [] } = useQuery({ queryKey: ['cours'], queryFn: fetchCours })

  const [matriculeEleve, setMatriculeEleve] = useState('')
  const [idCours, setIdCours] = useState('')
  const [dateAbsence, setDateAbsence] = useState(new Date().toISOString().split('T')[0])
  const [motif, setMotif] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
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
  }

  return (
    <Drawer open={open} onClose={onClose} title="Enregistrer une absence">
      <form onSubmit={handleSubmit} className="flex flex-col h-full">
        <div className="flex-1 overflow-y-auto space-y-4">
          <SearchableSelect
            label="Élève"
            value={matriculeEleve}
            onChange={setMatriculeEleve}
            options={eleves.map((el) => ({
              value: el.matricule,
              label: `${el.prenom} ${el.nom}`.trim(),
              sublabel: el.matricule,
            }))}
            placeholder="Rechercher un élève…"
            emptyMessage="Aucun élève trouvé"
          />

          <Select label="Cours (optionnel)" value={idCours} onChange={(e) => setIdCours(e.target.value)}>
            <option value="">— Aucun —</option>
            {cours.map((c) => (
              <option key={c.id} value={c.id}>{c.nom}</option>
            ))}
          </Select>

          <Input label="Date d'absence" type="date" value={dateAbsence} onChange={(e) => setDateAbsence(e.target.value)} max={new Date().toISOString().split('T')[0]} required />
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
