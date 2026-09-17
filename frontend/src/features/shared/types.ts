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
  lien_parente: string | null
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
  id_salle: number | null
  salle: { id: number; nom: string; capacite: number | null } | null
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
  created_at: string
  updated_at: string
}

export interface AffectationCoursClasse {
  id_classe: number
  coefficient: number
}

export interface AffectationCoursClasseResponse extends AffectationCoursClasse {
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
  coefficients: AffectationCoursClasseResponse[]
  enseignant: Enseignant | null
}

export interface Trimestre {
  id: number
  nom: string
  type: 'TRIMESTRE' | 'COMPOSITION'
  annee_scolaire_id: number
  date_debut: string
  date_fin: string
  verrouille: boolean
  created_at: string
  updated_at: string
}

export interface Enseignant {
  matricule: string
  nom: string
  prenom: string
  email: string
  telephone: string
  adresse: string
  specialite: string
  genre: string | null
  nina: string | null
  date_naissance: string | null
  categorie: string | null
  echelon: string | null
  fonction: string | null
  sf_nombre_enfants: string | null
  date_contrat: string | null
  classe_tenue: string | null
  dernier_poste: string | null
  date_arrivee_cap: string | null
  diplome: string | null
  observations: string | null
  created_at: string
  updated_at: string
}

export interface Paiement {
  id: number
  code_paiement: string | null
  id_inscription: number
  date: string
  montant: number
  mode: string | null
  observation: string | null
  matricule_eleve: string | null
  eleve_nom: string | null
  eleve_prenom: string | null
}
