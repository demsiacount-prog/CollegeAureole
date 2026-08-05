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

export interface AnneeScolaireCreateInput {
  libelle: string
  date_debut: string
  date_fin: string
  active?: boolean
}
