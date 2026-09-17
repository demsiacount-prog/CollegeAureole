export interface Utilisateur {
  id: number
  nom: string
  prenom: string
  email: string
  role: string
  actif: boolean
  created_at: string
  updated_at: string
}

export interface UtilisateurCreateInput {
  nom: string
  prenom: string
  email: string
  mot_de_passe: string
  role: string
}

export const ROLE_LABELS: Record<string, string> = {
  ADMIN: 'Admin',
  DIRECTEUR: 'Directeur',
  SECRETAIRE: 'Secrétaire',
  ENSEIGNANT: 'Enseignant',
  COMPTABLE: 'Comptable',
}

export const ROLE_OPTIONS = Object.entries(ROLE_LABELS).map(([value, label]) => ({ value, label }))