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
  village_quartier: string | null
  commune: string | null
  cercle: string | null
  statut_administratif: string | null
  type_ecole: string | null
  mode: string | null
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
  village_quartier?: string | null
  commune?: string | null
  cercle?: string | null
  statut_administratif?: string | null
  type_ecole?: string | null
  mode?: string | null
}

export interface EtablissementInfrastructures {
  id?: number
  id_annee_scolaire?: number | null
  salles_dur?: number | null
  salles_semi_dur?: number | null
  salles_banco?: number | null
  salles_autres?: number | null
  direction_dur?: number | null
  direction_banco?: number | null
  direction_autres?: number | null
  logement_direction?: number | null
  tables_bancs?: number | null
  chaises?: number | null
  armoires?: number | null
  tableaux?: number | null
  mobilier_divers?: number | null
}
