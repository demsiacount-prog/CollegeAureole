import { api } from '@/lib/api'
import type { Utilisateur, UtilisateurCreateInput } from './types'

export type { Utilisateur, UtilisateurCreateInput }

export async function fetchUtilisateurs(): Promise<Utilisateur[]> {
  const res = await api.get<Utilisateur[]>('/api/utilisateurs/')
  return res.data
}

export async function creerUtilisateur(body: UtilisateurCreateInput): Promise<Utilisateur> {
  const res = await api.post<Utilisateur>('/api/utilisateurs/', body)
  return res.data
}

export async function modifierStatutUtilisateur(id: number, actif: boolean): Promise<Utilisateur> {
  const res = await api.patch<Utilisateur>(`/api/utilisateurs/${id}/statut`, { actif })
  return res.data
}

export async function reinitialiserMotDePasse(id: number, nouveau_mot_de_passe: string): Promise<void> {
  await api.put(`/api/utilisateurs/${id}/mot-de-passe`, { nouveau_mot_de_passe })
}

export async function supprimerUtilisateur(id: number): Promise<void> {
  await api.delete(`/api/utilisateurs/${id}`)
}