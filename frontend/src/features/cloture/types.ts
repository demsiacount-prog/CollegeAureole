// Miroir de schemas/cloture.py

import type { StatutPassage } from '@/features/resultats/types'

export type { StatutPassage } from '@/features/resultats/types'

export interface ElevePreview {
  matricule: string
  nom: string
  prenom: string
  classe_id: number | null
  classe_nom: string | null
  niveau: string | null
  statut_passage: StatutPassage
  diplome: boolean
  action_prevue: string
  inscription_id: number
}

export interface CompteursPreview {
  ADMIS_PASSAGE: number
  ADMIS_DIPLOME: number
  RECALE_REDOUBLEMENT: number
  EXCLU: number
  EN_ATTENTE: number
}

export interface AnneeInfo {
  id: number
  libelle: string
}

export interface CloturePreview {
  annee_active: AnneeInfo | null
  total_eleves: number
  blocants: number
  peut_executer: boolean
  compteurs: CompteursPreview
  eleves: ElevePreview[]
}

export interface NouvelleAnneeInput {
  libelle: string
  date_debut: string
  date_fin: string
}

export interface RapportCloture {
  admis_passage: number
  admis_diplome: number
  recale_redoublement: number
  exclus: number
  total_traites: number
}

export interface ClotureExecuterResponse {
  succes: boolean
  ancienne_annee: AnneeInfo
  nouvelle_annee: AnneeInfo
  rapport: RapportCloture
}
