import type { Eleve } from '@/features/eleves/types'
import type { Cours } from '@/features/shared/types'

export interface Absence {
  id: number
  matricule_eleve: string
  id_cours: number | null
  date_absence: string
  justifiee: boolean
  motif: string | null
  justifiee_par_id: number | null
  date_justification: string | null
  created_at: string
  updated_at: string
  eleve: Eleve | null
  cours: Cours | null
}

export interface AlerteAbsence {
  matricule_eleve: string
  nom: string
  prenom: string
  nb_absences_non_justifiees: number
}

export interface AbsenceCreateInput {
  matricule_eleve: string
  id_cours?: number | null
  date_absence: string
  justifiee?: boolean
  motif?: string | null
}

export interface AbsenceJustifierInput {
  justifiee: boolean
  motif?: string | null
  utilisateur_id?: number | null
}
