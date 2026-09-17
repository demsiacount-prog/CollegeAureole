// Types miroir des schémas Pydantic du backend (schemas/utilisateurs.py)

export interface Utilisateur {
  id: number
  nom: string
  prenom: string
  email: string
  role?: string
  actif: boolean
  created_at: string
  updated_at: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  utilisateur: Utilisateur
}
