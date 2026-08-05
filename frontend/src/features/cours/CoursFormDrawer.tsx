import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Drawer } from '@/components/ui/Drawer'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { SearchableSelect } from '@/components/ui/SearchableSelect'
import { fetchClasses } from '@/features/classes/api'
import { fetchEnseignants } from '@/features/enseignants/api'
import type { Cours, CoursCreateInput } from './types'

interface Props {
  cours?: Cours | null
  open: boolean
  onClose: () => void
  onSubmit: (data: CoursCreateInput) => void
}

export default function CoursFormDrawer({ cours, open, onClose, onSubmit }: Props) {
  const isEdit = !!cours

  const { data: classes = [] } = useQuery({ queryKey: ['classes'], queryFn: fetchClasses })
  const { data: enseignants = [] } = useQuery({ queryKey: ['enseignants'], queryFn: () => fetchEnseignants() })

  const [nom, setNom] = useState('')
  const [description, setDescription] = useState('')
  const [volumeHoraire, setVolumeHoraire] = useState('')
  const [matriculeEnseignant, setMatriculeEnseignant] = useState<string>('')
  const [selectedClasses, setSelectedClasses] = useState<{ id: number; coefficient: number }[]>([])

  useEffect(() => {
    if (cours) {
      setNom(cours.nom)
      setDescription(cours.description)
      setVolumeHoraire(String(cours.volume_horaire))
      setMatriculeEnseignant(cours.matricule_enseignant ?? '')
      setSelectedClasses(cours.classes.map((cl) => ({
        id: cl.id,
        coefficient: cours.coefficients.find((c) => c.id_classe === cl.id)?.coefficient ?? 1,
      })))
    } else {
      setNom('')
      setDescription('')
      setVolumeHoraire('')
      setMatriculeEnseignant('')
      setSelectedClasses([])
    }
  }, [cours])

  const toggleClasse = (classeId: number) => {
    setSelectedClasses((prev) => {
      const exists = prev.find((c) => c.id === classeId)
      if (exists) return prev.filter((c) => c.id !== classeId)
      return [...prev, { id: classeId, coefficient: 1 }]
    })
  }

  const updateCoefficient = (classeId: number, coeff: string) => {
    setSelectedClasses((prev) =>
      prev.map((c) => (c.id === classeId ? { ...c, coefficient: Number(coeff) || 1 } : c))
    )
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit({
      nom,
      description,
      volume_horaire: Number(volumeHoraire),
      matricule_enseignant: matriculeEnseignant || null,
      affectations: selectedClasses.map((c) => ({ id_classe: c.id, coefficient: c.coefficient })),
    })
  }

  return (
    <Drawer open={open} onClose={onClose} title={isEdit ? 'Modifier le cours' : 'Nouveau cours'}>
      <form onSubmit={handleSubmit} className="flex flex-col h-full">
        <div className="flex-1 overflow-y-auto space-y-4">
          <Input label="Nom" placeholder="ex. Mathématiques" value={nom} onChange={(e) => setNom(e.target.value)} required />
          <Input label="Description" placeholder="ex. Algèbre et géométrie" value={description} onChange={(e) => setDescription(e.target.value)} required />
          <Input label="Volume horaire (h)" type="number" placeholder="ex. 4" value={volumeHoraire} onChange={(e) => setVolumeHoraire(e.target.value)} required />

          <SearchableSelect
            label="Enseignant"
            value={matriculeEnseignant}
            onChange={setMatriculeEnseignant}
            options={enseignants.map((e) => ({
              value: e.matricule,
              label: `${e.prenom} ${e.nom}`.trim(),
              sublabel: e.matricule,
            }))}
            placeholder="— Aucun —"
            emptyMessage="Aucun enseignant trouvé"
          />

          <div>
            <label className="block text-sm font-medium text-[var(--color-ink)] mb-1">Classes</label>
            {classes.length === 0 ? (
              <p className="text-sm text-[var(--color-ink-faint)]">Aucune classe disponible</p>
            ) : (
              <div className="space-y-2">
                {classes.map((cl) => {
                  const selected = selectedClasses.find((c) => c.id === cl.id)
                  return (
                    <div key={cl.id} className="flex items-center gap-3">
                      <input
                        type="checkbox"
                        checked={!!selected}
                        onChange={() => toggleClasse(cl.id)}
                        className="accent-[var(--color-brand)]"
                      />
                      <span className="text-sm text-[var(--color-ink)] flex-1">
                        {cl.niveau} — {cl.nom}
                      </span>
                      {selected && (
                        <Input
                          label=""
                          type="number"
                          value={String(selected.coefficient)}
                          onChange={(e) => updateCoefficient(cl.id, e.target.value)}
                          placeholder="Coeff."
                        />
                      )}
                    </div>
                  )
                })}
              </div>
            )}
          </div>
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
