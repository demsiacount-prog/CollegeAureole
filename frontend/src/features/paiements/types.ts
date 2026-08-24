export type { Paiement } from '@/features/shared/types'

export interface RemiseParEcheance {
  montant: number
  motif?: string | null
}

export interface PaiementCreateInput {
  id_inscription: number
  ids_echeances?: number[] | null
  montant: number
  date: string
  mode?: string | null
  observation?: string | null
  remises?: Record<number, RemiseParEcheance>
}

export interface PaiementUpdateInput {
  date?: string
  montant?: number
  mode?: string | null
  observation?: string | null
}

export interface PaiementResult {
  nb_paiements_crees: number
  echeances_mises_a_jour: Echeance[]
  reste_global: number
  credit_disponible: number
}

export interface Echeance {
  id: number
  id_inscription: number
  id_classe: number | null
  type_echeance: 'INSCRIPTION' | 'MENSUALITE'
  mois: string | null
  date_echeance: string
  montant_du: number
  montant_paye: number
  reste_a_payer: number
  statut: 'EN_ATTENTE' | 'PARTIEL' | 'SOLDE' | 'REPORTE'
  id_echeance_origine: number | null
  total_remises: number
}

export interface Relance extends Echeance {
  matricule_eleve: string | null
  eleve_nom: string | null
  eleve_prenom: string | null
  classe_nom: string | null
  niveau_classe: string | null
  code_tuteur: string | null
  tuteur_nom: string | null
  tuteur_prenom: string | null
  telephone_tuteur: string | null
  email_tuteur: string | null
}

export interface Remise {
  id: number
  id_echeance: number
  montant: number
  motif: string | null
  utilisateur_id: number | null
  utilisateur_nom: string | null
  utilisateur_prenom: string | null
  date: string
}

export interface RemiseCreateInput {
  montant: number
  motif?: string | null
  date: string
}

export interface PaiementGroupeInput {
  id_tuteur: number
  montant_total: number
  date: string
  mode?: string | null
  observation?: string | null
}

export interface PaiementGroupeResult {
  nb_enfants: number
  nb_paiements_crees: number
  reste_total: number
}
