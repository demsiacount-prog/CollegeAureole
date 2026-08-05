export interface Paiement {
  id: number
  code_paiement: string | null
  id_inscription: number
  date: string
  montant: number
  numero_recu: string | null
  mode: string | null
  observation: string | null
  matricule_eleve: string | null
  eleve_nom: string | null
  eleve_prenom: string | null
}

export interface PaiementCreateInput {
  id_inscription: number
  montant: number
  date: string
  mode?: string | null
  numero_recu?: string | null
  observation?: string | null
}

export interface PaiementResult {
  nb_paiements_crees: number
  numero_recu: string
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
