import { api } from '@/lib/api'
import type { Trimestre, TrimestreCreateInput } from './types'

export type { Trimestre, TrimestreCreateInput }

export async function fetchTrimestres(anneeScolaireId?: number): Promise<Trimestre[]> {
  const params: Record<string, number> = {}
  if (anneeScolaireId) params.annee_scolaire_id = anneeScolaireId
  const res = await api.get<Trimestre[]>('/api/trimestres/', { params })
  return res.data
}

export async function createTrimestre(body: TrimestreCreateInput): Promise<Trimestre> {
  const res = await api.post<Trimestre>('/api/trimestres/', body)
  return res.data
}

export async function deleteTrimestre(id: number): Promise<void> {
  await api.delete(`/api/trimestres/${id}`)
}

export async function verrouillerTrimestre(id: number): Promise<Trimestre> {
  const res = await api.put<Trimestre>(`/api/trimestres/${id}/verrouiller`)
  return res.data
}

export async function deverrouillerTrimestre(id: number): Promise<Trimestre> {
  const res = await api.put<Trimestre>(`/api/trimestres/${id}/deverrouiller`)
  return res.data
}

export async function genererPeriodesParDefaut(anneeScolaireId: number): Promise<{ cree: number }> {
  const res = await api.post<{ cree: number }>('/api/trimestres/generer', { annee_scolaire_id: anneeScolaireId })
  return res.data
}
