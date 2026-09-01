export interface Etablissement {
  id: number
  nom: string
  sigle: string | null
  devise: string | null
  adresse: string | null
  telephone: string | null
  email: string | null
  logo: string | null
  date_initialisation: string | null
  academie: string | null
  cap: string | null
  created_at: string | null
  updated_at: string | null
}

export interface EtablissementUpdate {
  nom: string
  sigle?: string | null
  devise?: string | null
  adresse?: string | null
  telephone?: string | null
  email?: string | null
  logo?: string | null
  academie?: string | null
  cap?: string | null
}
