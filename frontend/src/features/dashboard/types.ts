export interface MoyenneClasse {
  classe: string
  moy: number
  bareme: number
}

export interface RepartitionNiveau {
  name: string
  value: number
}

export interface AbsenceMois {
  mois: string
  absences: number
}

export interface ActiviteRecente {
  type: string
  texte: string
  date: string
}

export interface DashboardStatsResponse {
  nb_eleves: number
  nb_enseignants: number
  nb_classes: number
  taux_absence: number
  absences_7_jours: number
  paiements_mois: number
  moyennes_par_classe: MoyenneClasse[]
  repartition_niveaux: RepartitionNiveau[]
  absences_par_mois: AbsenceMois[]
  dernieres_activites: ActiviteRecente[]
}

export interface EvolutionMensuelle {
  mois: string
  paiements: number
  depenses: number
}

export interface DashboardFinanceResponse {
  paiements_mois: number
  depenses_mois: number
  solde_mois: number
  echeances_en_retard: number
  montant_en_retard: number
  evolution_mensuelle: EvolutionMensuelle[]
  dernieres_activites: ActiviteRecente[]
}
