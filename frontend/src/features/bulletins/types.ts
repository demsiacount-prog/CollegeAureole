export interface BulletinDetail {
  id: number
  id_cours: number
  cours_nom: string
  moyenne: number
  coefficient: number
  created_at: string
  updated_at: string
}

export interface Bulletin {
  id: number
  matricule_eleve: string
  id_trimestre: number
  id_classe: number
  moyenne_generale: number
  rang: number | null
  appreciation: string | null
  statut: 'BROUILLON' | 'PUBLIE'
  generated_at: string
  published_at: string | null
  created_at: string
  updated_at: string
  details: BulletinDetail[]
  eleve?: {
    matricule: string
    nom: string
    prenom: string
    photo: string | null
  } | null
}

export interface BulletinDetailFull extends Bulletin {
  eleve: {
    matricule: string
    nom: string
    prenom: string
    photo: string | null
    classe: { id: number; niveau: string; nom: string } | null
  }
  trimestre: {
    id: number
    nom: string
    type: 'TRIMESTRE' | 'COMPOSITION'
    date_debut: string
    date_fin: string
    annee_scolaire_id: number
  }
  classe: {
    id: number
    niveau: string
    nom: string
  }
}

export interface BulletinGenerateInput {
  matricule_eleve: string
  id_trimestre: number
}

export interface BulletinGenerateClasseInput {
  id_classe: number
  id_trimestre: number
}

export interface BulletinPublierInput {
  id_classe: number
  id_trimestre: number
}
