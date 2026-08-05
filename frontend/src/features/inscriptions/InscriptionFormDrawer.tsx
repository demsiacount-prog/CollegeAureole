import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Drawer } from '@/components/ui/Drawer'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { SearchableSelect } from '@/components/ui/SearchableSelect'
import { fetchEleves } from '@/features/eleves/api'
import { fetchClasses } from '@/features/classes/api'
import { fetchAnneesScolaires } from '@/features/annees_scolaires/api'
import type { InscriptionCreateInput } from './types'

interface Props {
  open: boolean
  onClose: () => void
  onSubmit: (data: InscriptionCreateInput) => void
}

export default function InscriptionFormDrawer({ open, onClose, onSubmit }: Props) {
  const { data: eleves = [] } = useQuery({ queryKey: ['eleves', 'select'], queryFn: () => fetchEleves({ limit: 500 }) })
  const { data: classes = [] } = useQuery({ queryKey: ['classes'], queryFn: fetchClasses })
  const { data: annees = [] } = useQuery({ queryKey: ['annees-scolaires'], queryFn: fetchAnneesScolaires })

  const [matriculeEleve, setMatriculeEleve] = useState('')
  const [idClasse, setIdClasse] = useState('')
  const [idAnneeScolaire, setIdAnneeScolaire] = useState('')
  const [observation, setObservation] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit({
      matricule_eleve: matriculeEleve,
      id_classe: idClasse ? Number(idClasse) : null,
      id_annee_scolaire: Number(idAnneeScolaire),
      observation: observation || null,
    })
    setMatriculeEleve('')
    setIdClasse('')
    setIdAnneeScolaire('')
    setObservation('')
  }

  return (
    <Drawer open={open} onClose={onClose} title="Nouvelle inscription">
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

          <Select label="Année scolaire" value={idAnneeScolaire} onChange={(e) => setIdAnneeScolaire(e.target.value)} required>
            <option value="">— Sélectionner —</option>
            {annees.map((a) => (
              <option key={a.id} value={a.id}>{a.libelle}</option>
            ))}
          </Select>

          <Select label="Classe (optionnel)" value={idClasse} onChange={(e) => setIdClasse(e.target.value)}>
            <option value="">— Aucune —</option>
            {classes.map((c) => (
              <option key={c.id} value={c.id}>{c.niveau} — {c.nom}</option>
            ))}
          </Select>

          <Input label="Observation (optionnel)" placeholder="ex. Redoublant" value={observation} onChange={(e) => setObservation(e.target.value)} />
        </div>

        <div className="p-4 border-t border-[var(--color-border)]">
          <Button type="submit" variant="primary" className="w-full">
            Inscrire
          </Button>
        </div>
      </form>
    </Drawer>
  )
}
