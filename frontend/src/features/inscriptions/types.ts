export interface Inscription {
  id: number
  code_inscription: string | null
  matricule_eleve: string
  id_classe: number | null
  id_annee_scolaire: number
  statut: string
  statut_passage: string
  diplome: boolean
  montant_total: number
  credit_disponible: number
  date_inscription: string
  date_fin: string | null
  observation: string | null
  created_at: string
  updated_at: string
  eleve_nom: string | null
  eleve_prenom: string | null
}

import type { Paiement } from '@/features/shared/types'
import type { MoyenneTrimestre, NoteParMatiere } from '@/features/eleves/types'

export type { MoyenneTrimestre, NoteParMatiere }

export interface InscriptionDetail extends Inscription {
  classe: { id: number; niveau: string; nom: string } | null
  annee_scolaire: { id: number; libelle: string } | null
  eleve: { matricule: string; nom: string; prenom: string } | null
  nb_absences: number
  moyenne_annuelle: number | null
  moyennes_par_trimestre: MoyenneTrimestre[]
  paiements: Paiement[]
  montant_paye: number
  reste_a_payer: number
  notes_par_matiere: NoteParMatiere[]
}

export interface InscriptionCreateInput {
  matricule_eleve: string
  id_classe: number | null
  id_annee_scolaire: number
  statut?: string
  montant_total?: number
  date_inscription?: string
  observation?: string | null
}
