import type { Role } from '@/types'

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

export const ROLES: { value: Role; label: string }[] = [
  { value: 'admin', label: 'Administrateur' },
  { value: 'directeur', label: 'Directeur' },
  { value: 'comptable', label: 'Comptable' },
]

export const ROLE_LABELS: Record<Role, string> = {
  admin: 'Administrateur',
  directeur: 'Directeur',
  comptable: 'Comptable',
}

export interface UtilisateurCreateInput {
  nom: string
  prenom: string
  email: string
  mot_de_passe: string
  role: Role
}

export interface UtilisateurUpdateInput {
  nom: string
  prenom: string
  email: string
  role: Role
  actif: boolean
}
