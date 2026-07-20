// Types miroir des schémas Pydantic du backend (schemas/utilisateurs.py, enums/roles.py)

export type Role = 'admin' | 'directeur' | 'comptable'

export interface Utilisateur {
  id: number
  nom: string
  prenom: string
  email: string
  role: Role
  actif: boolean
  created_at: string
  updated_at: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  utilisateur: Utilisateur
}

export interface ApiError {
  detail: string
}
