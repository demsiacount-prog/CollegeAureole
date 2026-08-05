import { api } from '@/lib/api'
import type { Utilisateur, UtilisateurCreateInput, UtilisateurUpdateInput } from './types'

export type { Utilisateur, UtilisateurCreateInput, UtilisateurUpdateInput }

export async function fetchUtilisateurs(): Promise<Utilisateur[]> {
  const res = await api.get<Utilisateur[]>('/api/utilisateurs/')
  return res.data
}

export async function createUtilisateur(body: UtilisateurCreateInput): Promise<Utilisateur> {
  const res = await api.post<Utilisateur>('/api/utilisateurs/', body)
  return res.data
}

export async function updateUtilisateur(id: number, body: UtilisateurUpdateInput): Promise<Utilisateur> {
  const res = await api.put<Utilisateur>(`/api/utilisateurs/${id}`, body)
  return res.data
}

export async function deleteUtilisateur(id: number): Promise<void> {
  await api.delete(`/api/utilisateurs/${id}`)
}
