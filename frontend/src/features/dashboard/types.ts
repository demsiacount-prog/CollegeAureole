export interface MoyenneClasse {
  classe: string
  moy: number
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
