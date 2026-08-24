import { useEffect, useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Drawer } from '@/components/ui/Drawer'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { fetchClasseDetail } from '@/features/notes/api'
import { fetchCours } from '@/features/cours/api'
import { fetchClasses } from '@/features/classes/api'
import { fetchSalles } from '@/features/salles/api'
import { fetchAnneesScolaires } from '@/features/annees_scolaires/api'
import { required, heureFinApresDebut, validateFields, hasErrors, type Errors } from '@/lib/validation'
import type { SeanceCreateInput } from './types'

const JOURS = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi'] as const

interface Props {
  open: boolean
  onClose: () => void
  onSubmit: (data: SeanceCreateInput) => void
  initial?: SeanceCreateInput | null
}

export default function SeanceFormDrawer({ open, onClose, onSubmit, initial }: Props) {
  const [idCours, setIdCours] = useState('')
  const [idClasse, setIdClasse] = useState('')
  const [idAnneeScolaire, setIdAnneeScolaire] = useState('')
  const [idSalle, setIdSalle] = useState('')
  const [jour, setJour] = useState('')
  const [heureDebut, setHeureDebut] = useState('')
  const [heureFin, setHeureFin] = useState('')
  const [errors, setErrors] = useState<Errors>({})
  const classeInitialeRef = useRef<string>('')

  const { data: cours = [] } = useQuery({ queryKey: ['cours'], queryFn: fetchCours })
  const { data: classes = [] } = useQuery({ queryKey: ['classes'], queryFn: fetchClasses })
  const { data: salles = [] } = useQuery({ queryKey: ['salles'], queryFn: fetchSalles })
  const { data: annees = [] } = useQuery({ queryKey: ['annees-scolaires'], queryFn: fetchAnneesScolaires })
  const { data: classeDetail, isLoading: loadingClasse } = useQuery({
    queryKey: ['classe-detail', idClasse],
    queryFn: () => fetchClasseDetail(Number(idClasse)),
    enabled: !!idClasse,
  })

  useEffect(() => {
    if (open) {
      if (initial) {
        classeInitialeRef.current = String(initial.id_classe)
        setIdCours(String(initial.id_cours))
        setIdClasse(String(initial.id_classe))
        setIdAnneeScolaire(String(initial.id_annee_scolaire))
        setIdSalle(initial.id_salle ? String(initial.id_salle) : '')
        setJour(initial.jour_semaine)
        setHeureDebut(initial.heure_debut)
        setHeureFin(initial.heure_fin)
      } else {
        classeInitialeRef.current = ''
        setIdCours('')
        setIdClasse('')
        setIdAnneeScolaire('')
        setIdSalle('')
        setJour('')
        setHeureDebut('')
        setHeureFin('')
      }
      setErrors({})
    }
  }, [open, initial])

  useEffect(() => {
    if (annees.length > 0 && !idAnneeScolaire) {
      const active = annees.find((a) => a.active)
      if (active) setIdAnneeScolaire(active.id.toString())
    }
  }, [annees, idAnneeScolaire])

  useEffect(() => {
    if (!idClasse || idClasse === classeInitialeRef.current) return
    if (idCours && classeDetail && classeDetail.cours.some((c) => c.id === Number(idCours))) return
    setIdCours('')
  }, [idClasse, classeDetail, idCours])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const errs = validateFields({
      id_annee_scolaire: required(idAnneeScolaire, "L'année scolaire"),
      id_classe: required(idClasse, 'La classe'),
      id_cours: required(idCours, 'Le cours'),
      jour: required(jour, 'Le jour'),
      heure_debut: required(heureDebut, "L'heure de début"),
      heure_fin: required(heureFin, "L'heure de fin") ?? heureFinApresDebut(heureDebut, heureFin),
    })
    setErrors(errs)
    if (hasErrors(errs)) return
    onSubmit({
      id_cours: Number(idCours),
      id_classe: Number(idClasse),
      id_annee_scolaire: Number(idAnneeScolaire),
      id_salle: idSalle ? Number(idSalle) : null,
      jour_semaine: jour as import('./types').JourSemaine,
      heure_debut: heureDebut,
      heure_fin: heureFin,
    })
  }

  return (
    <Drawer open={open} onClose={onClose} title={initial ? 'Modifier la séance' : 'Nouvelle séance'}>
      <form onSubmit={handleSubmit} noValidate className="flex flex-col h-full">
        <div className="flex-1 overflow-y-auto space-y-4">
          <Select label="Année scolaire" value={idAnneeScolaire} onChange={(e) => { setIdAnneeScolaire(e.target.value); if (errors.id_annee_scolaire) setErrors((prev) => ({ ...prev, id_annee_scolaire: undefined })) }} required error={errors.id_annee_scolaire}>
            <option value="">— Sélectionner —</option>
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

          {idClasse && (
            <p className="text-xs text-[var(--color-ink-dim)]">
              Effectif de la classe : <strong>{loadingClasse ? '…' : classeDetail?.effectif_actuel ?? '?'}</strong> élève(s)
            </p>
          )}

          <Select label="Cours" value={idCours} onChange={(e) => { setIdCours(e.target.value); if (errors.id_cours) setErrors((prev) => ({ ...prev, id_cours: undefined })) }} required error={errors.id_cours}>
            <option value="">— Sélectionner —</option>
            {classeDetail?.cours && classeDetail.cours.length > 0
              ? classeDetail.cours.map((c) => (
                  <option key={c.id} value={c.id}>{c.nom}</option>
                ))
              : cours.map((c) => (
                  <option key={c.id} value={c.id}>{c.nom}</option>
                ))}
          </Select>

          <Select label="Salle (optionnel)" value={idSalle} onChange={(e) => setIdSalle(e.target.value)}>
            <option value="">— Aucune —</option>
            {salles.map((s) => {
              const tropPetite = classeDetail && s.capacite != null && classeDetail.effectif_actuel > s.capacite
              return (
                <option key={s.id} value={s.id} disabled={tropPetite}>
                  {s.nom}{s.capacite ? ` (${s.capacite} places)` : ''}
                  {tropPetite ? ' — insuffisante' : ''}
                </option>
              )
            })}
          </Select>
          {idSalle && classeDetail && (() => {
            const salle = salles.find((s) => s.id === Number(idSalle))
            if (!salle || salle.capacite == null) return null
            if (classeDetail.effectif_actuel > salle.capacite) {
              return (
                <p className="text-xs text-[var(--color-danger)]">
                  Cette salle ({salle.capacite} places) est trop petite pour l'effectif de {classeDetail.effectif_actuel} élèves.
                </p>
              )
            }
            return null
          })()}

          <Select label="Jour" value={jour} onChange={(e) => { setJour(e.target.value); if (errors.jour) setErrors((prev) => ({ ...prev, jour: undefined })) }} required error={errors.jour}>
            <option value="">— Sélectionner —</option>
            {JOURS.map((j) => (
              <option key={j} value={j}>{j}</option>
            ))}
          </Select>

          <div className="grid grid-cols-2 gap-3">
            <Input label="Heure de début" type="time" value={heureDebut} onChange={(e) => { setHeureDebut(e.target.value); if (errors.heure_debut) setErrors((prev) => ({ ...prev, heure_debut: undefined, heure_fin: undefined })) }} required error={errors.heure_debut} />
            <Input label="Heure de fin" type="time" value={heureFin} onChange={(e) => { setHeureFin(e.target.value); if (errors.heure_fin) setErrors((prev) => ({ ...prev, heure_fin: undefined })) }} required error={errors.heure_fin} />
          </div>
        </div>

        <div className="p-4 border-t border-[var(--color-border)]">
          <Button type="submit" variant="primary" className="w-full">
            {initial ? 'Enregistrer' : 'Créer'}
          </Button>
        </div>
      </form>
    </Drawer>
  )
}
