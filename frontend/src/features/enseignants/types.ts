export interface Enseignant {
  matricule: string
  nom: string
  prenom: string
  email: string
  telephone: string
  adresse: string
  specialite: string
  heures_hebdo_max: number | null
  created_at: string
  updated_at: string
}

export interface EnseignantCreateInput {
  nom: string
  prenom: string
  email: string
  telephone: string
  adresse: string
  specialite: string
  heures_hebdo_max?: number | null
}

export interface EnseignantDossier {
  enseignant: Enseignant
  stats: {
    nb_annees: number
    nb_classes_distinctes: number
    nb_matieres_distinctes: number
  }
  historique: AnneeHistorique[]
}

export interface AnneeHistorique {
  annee_scolaire: {
    id: number
    libelle: string
    date_debut: string
    date_fin: string
    active: boolean
    cloturee: boolean
  } | null
  affectations: AffectationHistorique[]
}

export interface AffectationHistorique {
  classe: {
    id: number
    niveau: string
    nom: string
  } | null
  cours: {
    id: number
    nom: string
    description: string
    volume_horaire: number
    created_at: string
    updated_at: string
  }
}
