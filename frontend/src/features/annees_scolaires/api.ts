import { api } from '@/lib/api'
import type { AnneeScolaire, AnneeScolaireCreateInput } from './types'

export type { AnneeScolaire, AnneeScolaireCreateInput }

export async function fetchAnneesScolaires(): Promise<AnneeScolaire[]> {
  const res = await api.get<AnneeScolaire[]>('/api/anneesScolaires/')
  return res.data
}

export async function createAnneeScolaire(body: AnneeScolaireCreateInput): Promise<AnneeScolaire> {
  const res = await api.post<AnneeScolaire>('/api/anneesScolaires/', body)
  return res.data
}

export async function deleteAnneeScolaire(id: number): Promise<void> {
  await api.delete(`/api/anneesScolaires/${id}`)
}

export async function activerAnneeScolaire(id: number): Promise<AnneeScolaire> {
  const res = await api.put<AnneeScolaire>(`/api/anneesScolaires/${id}/activer`)
  return res.data
}

export async function cloturerAnneeScolaire(id: number): Promise<AnneeScolaire> {
  const res = await api.put<AnneeScolaire>(`/api/anneesScolaires/${id}/cloturer`)
  return res.data
}
