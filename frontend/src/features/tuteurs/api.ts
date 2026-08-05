import { api } from '@/lib/api'
import type { Tuteur, TuteurDetail } from '@/features/shared/types'

export interface TuteurCreateInput {
  nom: string
  prenom: string
  email: string
  telephone: string
  adresse: string
  profession: string
}

export async function fetchTuteurs(params?: { q?: string; skip?: number; limit?: number }): Promise<Tuteur[]> {
  const res = await api.get<Tuteur[]>('/api/tuteurs/', { params: { limit: 500, ...params } })
  return res.data
}

export async function fetchTuteursTotal(q?: string): Promise<number> {
  const res = await api.get<{ total: number }>('/api/tuteurs/compte', { params: { q } })
  return res.data.total
}

export async function fetchTuteurById(id: number): Promise<TuteurDetail> {
  const res = await api.get<TuteurDetail>(`/api/tuteurs/${id}`)
  return res.data
}

export async function createTuteur(body: TuteurCreateInput): Promise<Tuteur> {
  const res = await api.post<Tuteur>('/api/tuteurs/', body)
  return res.data
}

export async function updateTuteur(id: number, body: TuteurCreateInput): Promise<Tuteur> {
  const res = await api.put<Tuteur>(`/api/tuteurs/${id}`, body)
  return res.data
}

export async function deleteTuteur(id: number): Promise<void> {
  await api.delete(`/api/tuteurs/${id}`)
}
