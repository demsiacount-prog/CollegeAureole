export interface Salle {
  id: number
  code_salle: string | null
  nom: string
  capacite: number | null
  created_at: string
  updated_at: string
}

export interface SalleCreateInput {
  nom: string
  capacite?: number | null
}
