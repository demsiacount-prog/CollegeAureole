import { api } from '@/lib/api'
import type { Enseignant, EnseignantCreateInput, EnseignantDossier } from './types'

export async function fetchEnseignants(params?: { q?: string; skip?: number; limit?: number }): Promise<Enseignant[]> {
  const res = await api.get<Enseignant[]>('/api/enseignants/', { params: { limit: 500, ...params } })
  return res.data
}

export async function fetchEnseignantsTotal(q?: string): Promise<number> {
  const res = await api.get<{ total: number }>('/api/enseignants/compte', { params: { q } })
  return res.data.total
}

export async function fetchEnseignantDossier(matricule: string): Promise<EnseignantDossier> {
  const res = await api.get<EnseignantDossier>(`/api/enseignants/${matricule}/dossier`)
  return res.data
}

export async function createEnseignant(body: EnseignantCreateInput): Promise<Enseignant> {
  const res = await api.post<Enseignant>('/api/enseignants/', body)
  return res.data
}

export async function updateEnseignant(matricule: string, body: EnseignantCreateInput): Promise<Enseignant> {
  const res = await api.put<Enseignant>(`/api/enseignants/${matricule}`, body)
  return res.data
}

export async function deleteEnseignant(matricule: string): Promise<void> {
  await api.delete(`/api/enseignants/${matricule}`)
}
