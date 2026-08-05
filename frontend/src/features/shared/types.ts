// Types miroir des schémas Pydantic référencés par plusieurs modules.

export interface Tuteur {
  id: number
  code_tuteur: string | null
  nom: string
  prenom: string
  email: string
  telephone: string
  adresse: string
  profession: string
  created_at: string
  updated_at: string
}

export interface TuteurDetail extends Tuteur {
  eleves: EleveResume[]
}

export interface EleveResume {
  matricule: string
  nom: string
  prenom: string
  photo: string | null
  date_de_naissance: string
  sexe: string
  statut: string
  classe: Classe | null
}

export interface Classe {
  id: number
  code_classe: string | null
  niveau: string
  nom: string
  frais_inscription: number
  mensualite: number
  created_at: string
  updated_at: string
}

export interface AnneeScolaire {
  id: number
  libelle: string
  date_debut: string
  date_fin: string
  active: boolean
  cloturee: boolean
}

export interface AffectationCoursClasse {
  id_classe: number
  coefficient: number
  created_at: string
  updated_at: string
}

export interface Cours {
  id: number
  code_cours: string | null
  nom: string
  description: string
  volume_horaire: number
  matricule_enseignant: string | null
  created_at: string
  updated_at: string
  classes: Classe[]
  coefficients: AffectationCoursClasse[]
  enseignant: Enseignant | null
}

export interface Trimestre {
  id: number
  nom: string
  type: 'TRIMESTRE' | 'COMPOSITION'
  annee_scolaire_id: number
  date_debut: string
  date_fin: string
}

export interface Enseignant {
  matricule: string
  nom: string
  prenom: string
}

export interface Paiement {
  id: number
  code_paiement: string | null
  id_inscription: number
  date: string
  montant: number
  numero_recu: string | null
  mode: string | null
  observation: string | null
}
