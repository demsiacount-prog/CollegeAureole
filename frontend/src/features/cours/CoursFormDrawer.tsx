import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Drawer } from '@/components/ui/Drawer'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { SearchableSelect } from '@/components/ui/SearchableSelect'
import { fetchClasses } from '@/features/classes/api'
import { fetchEnseignants } from '@/features/enseignants/api'
import { required, positiveNumber, validateFields, hasErrors, type Errors } from '@/lib/validation'
import { baremeNiveau } from '@/lib/bareme'
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
  const [errors, setErrors] = useState<Errors>({})

  // Réinitialisé à CHAQUE ouverture ([open, cours]) : dépendre uniquement de
  // `cours` laissait les saisies non enregistrées d'une session précédente
  // quand on rouvre le même cours.
  useEffect(() => {
    if (!open) return
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
    setErrors({})
  }, [open, cours])

  const toggleClasse = (classeId: number) => {
    setSelectedClasses((prev) => {
      const exists = prev.find((c) => c.id === classeId)
      if (exists) return prev.filter((c) => c.id !== classeId)
      return [...prev, { id: classeId, coefficient: 1 }]
    })
    if (errors.classes) setErrors((prev) => ({ ...prev, classes: undefined }))
  }

  const updateCoefficient = (classeId: number, coeff: string) => {
    setSelectedClasses((prev) =>
      prev.map((c) => (c.id === classeId ? { ...c, coefficient: Number(coeff) || 1 } : c))
    )
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const errs = validateFields({
      nom: required(nom, 'Le nom'),
      description: required(description, 'La description'),
      volume_horaire: positiveNumber(volumeHoraire, 'Le volume horaire'),
      classes: selectedClasses.length > 0 ? undefined : 'Sélectionnez au moins une classe.',
    })
    setErrors(errs)
    if (hasErrors(errs)) return
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
      <form onSubmit={handleSubmit} noValidate className="flex flex-col h-full">
        <div className="flex-1 overflow-y-auto space-y-4">
          <Input
            label="Nom"
            placeholder="ex. Mathématiques"
            value={nom}
            onChange={(e) => {
              setNom(e.target.value)
              if (errors.nom) setErrors((prev) => ({ ...prev, nom: undefined }))
            }}
            required
            error={errors.nom}
          />
          <Input
            label="Description"
            placeholder="ex. Algèbre et géométrie"
            value={description}
            onChange={(e) => {
              setDescription(e.target.value)
              if (errors.description) setErrors((prev) => ({ ...prev, description: undefined }))
            }}
            required
            error={errors.description}
          />
          <Input
            label="Volume horaire (h)"
            type="number"
            placeholder="ex. 4"
            value={volumeHoraire}
            onChange={(e) => {
              setVolumeHoraire(e.target.value)
              if (errors.volume_horaire) setErrors((prev) => ({ ...prev, volume_horaire: undefined }))
            }}
            required
            error={errors.volume_horaire}
          />

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
            <p className="mb-3 text-xs text-[var(--color-ink-faint)]">
              Cochez les classes où la matière est enseignée. Le coefficient ne concerne que le second cycle
              (notes /20) ; il est fixé à 1 pour les classes du premier cycle (notes /10, moyenne simple).
            </p>
            {errors.classes && <p className="mb-1 text-xs text-[var(--color-danger)]">{errors.classes}</p>}
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
                      {selected && baremeNiveau(cl.niveau) !== 10 && (
                        <div className="flex items-center gap-2">
                          <label
                            htmlFor={`coeff-${cl.id}`}
                            className="text-xs font-medium text-[var(--color-ink-dim)]"
                          >
                            Coefficient
                          </label>
                          <input
                            id={`coeff-${cl.id}`}
                            type="number"
                            min={0.5}
                            step={0.5}
                            value={String(selected.coefficient)}
                            onChange={(e) => updateCoefficient(cl.id, e.target.value)}
                            placeholder="1"
                            aria-label={`Coefficient pour ${cl.niveau} — ${cl.nom}`}
                            className="h-8 w-20 rounded-[var(--radius-sm)] border border-[var(--color-border)] bg-[var(--color-surface-2)] px-2 text-center text-sm text-[var(--color-ink)] placeholder:text-[var(--color-ink-faint)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-halo)]"
                          />
                        </div>
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
