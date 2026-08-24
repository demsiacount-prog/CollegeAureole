import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Drawer } from '@/components/ui/Drawer'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { SearchableSelect } from '@/components/ui/SearchableSelect'
import { fetchEleves } from '@/features/eleves/api'
import { fetchClasses } from '@/features/classes/api'
import { fetchAnneesScolaires } from '@/features/annees_scolaires/api'
import { required, validateFields, hasErrors, type Errors } from '@/lib/validation'
import { extractErrorMessage } from '@/lib/api'
import type { InscriptionCreateInput } from './types'

interface Props {
  open: boolean
  onClose: () => void
  onSubmit: (data: InscriptionCreateInput) => void
  initialMatricule?: string
  initialAnneeScolaireId?: number | null
}

export default function InscriptionFormDrawer({ open, onClose, onSubmit, initialMatricule, initialAnneeScolaireId }: Props) {
  const { data: eleves = [] } = useQuery({ queryKey: ['eleves', 'select'], queryFn: () => fetchEleves({ limit: 5000 }) })
  const { data: classes = [] } = useQuery({ queryKey: ['classes'], queryFn: fetchClasses })
  const { data: annees = [] } = useQuery({ queryKey: ['annees-scolaires'], queryFn: fetchAnneesScolaires })

  const activeAnneeId = annees.find((a) => a.active)?.id

  const [matriculeEleve, setMatriculeEleve] = useState(initialMatricule ?? '')
  const [idClasse, setIdClasse] = useState('')
  const [idAnneeScolaire, setIdAnneeScolaire] = useState(initialAnneeScolaireId != null ? String(initialAnneeScolaireId) : activeAnneeId != null ? String(activeAnneeId) : '')
  const [observation, setObservation] = useState('')
  const [errors, setErrors] = useState<Errors>({})
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [enCours, setEnCours] = useState(false)

  useEffect(() => {
    if (open) {
      setMatriculeEleve(initialMatricule ?? '')
      setIdAnneeScolaire(initialAnneeScolaireId != null ? String(initialAnneeScolaireId) : activeAnneeId != null ? String(activeAnneeId) : '')
      setIdClasse('')
      setObservation('')
      setErrors({})
      setSubmitError(null)
    }
  }, [open, initialMatricule, initialAnneeScolaireId, activeAnneeId])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const errs = validateFields({
      matricule_eleve: required(matriculeEleve, "L'élève"),
      id_classe: required(idClasse, "La classe"),
    })
    setErrors(errs)
    if (hasErrors(errs)) return
    setEnCours(true)
    setSubmitError(null)
    try {
      await onSubmit({
        matricule_eleve: matriculeEleve,
        id_classe: Number(idClasse),
        id_annee_scolaire: Number(idAnneeScolaire),
        observation: observation || null,
      })
      // Succès : le parent referme le drawer ; on réinitialise pour une
      // éventuelle réutilisation du composant.
      setMatriculeEleve('')
      setIdClasse('')
      setIdAnneeScolaire('')
      setObservation('')
      setErrors({})
    } catch (err) {
      // Échec : les champs sont conservés pour correction, message clair.
      setSubmitError(
        extractErrorMessage(err, "L'inscription n'a pas pu être enregistrée. Vérifiez les informations puis réessayez."),
      )
    } finally {
      setEnCours(false)
    }
  }

  return (
    <Drawer open={open} onClose={onClose} title="Nouvelle inscription">
      <form onSubmit={handleSubmit} noValidate className="flex flex-col h-full">
        <div className="flex-1 overflow-y-auto space-y-4">
          <SearchableSelect
            label="Élève"
            value={matriculeEleve}
            onChange={(v) => {
              setMatriculeEleve(v)
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

          <Select label="Année scolaire" value={idAnneeScolaire} onChange={(e) => { setIdAnneeScolaire(e.target.value); if (errors.id_annee_scolaire) setErrors((prev) => ({ ...prev, id_annee_scolaire: undefined })) }} required error={errors.id_annee_scolaire}>
            {annees.map((a) => (
              <option key={a.id} value={a.id}>{a.libelle}</option>
            ))}
          </Select>

          <Select label="Classe" value={idClasse} onChange={(e) => { setIdClasse(e.target.value); if (errors.id_classe) setErrors((prev) => ({ ...prev, id_classe: undefined })) }} required error={errors.id_classe}>
            <option value="">— Sélectionner —</option>
            {classes.map((c) => (
              <option key={c.id} value={c.id}>{c.niveau} — {c.nom}</option>
            ))}
          </Select>

          <Input label="Observation (optionnel)" placeholder="ex. Redoublant" value={observation} onChange={(e) => setObservation(e.target.value)} />

          {submitError && (
            <p role="alert" className="rounded-[var(--radius-sm)] border border-[var(--color-danger)]/20 bg-[var(--color-danger)]/10 px-3 py-2 text-sm text-[var(--color-danger)]">
              {submitError}
            </p>
          )}
        </div>

        <div className="p-4 border-t border-[var(--color-border)]">
          <Button type="submit" variant="primary" className="w-full" disabled={enCours}>
            {enCours ? 'Enregistrement…' : 'Inscrire'}
          </Button>
        </div>
      </form>
    </Drawer>
  )
}
