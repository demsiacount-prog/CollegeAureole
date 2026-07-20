// Types miroir des schémas Pydantic référencés par plusieurs modules.

export interface Tuteur {
  id: number
  nom: string
  prenom: string
  email: string
  telephone: string
  adresse: string
  profession: string
}

export interface Classe {
  id: number
  niveau: string
  nom: string
  frais_inscription: number
  mensualite: number
  capacite_max: number | null
}

export interface AnneeScolaire {
  id: number
  libelle: string
  date_debut: string
  date_fin: string
  active: boolean
  cloturee: boolean
}

export interface Cours {
  id: number
  nom: string
}

export interface Trimestre {
  id: number
  nom: string
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
  id_inscription: number
  date: string
  montant: number
  numero_recu: string | null
  mode: string | null
  observation: string | null
}
