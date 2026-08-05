import { api } from '@/lib/api'
import type { Salle, SalleCreateInput } from './types'

export type { Salle, SalleCreateInput }

export async function fetchSalles(): Promise<Salle[]> {
  const res = await api.get<Salle[]>('/api/salles/')
  return res.data
}

export async function createSalle(body: SalleCreateInput): Promise<Salle> {
  const res = await api.post<Salle>('/api/salles/', body)
  return res.data
}

export async function updateSalle(id: number, body: SalleCreateInput): Promise<Salle> {
  const res = await api.put<Salle>(`/api/salles/${id}`, body)
  return res.data
}

export async function deleteSalle(id: number): Promise<void> {
  await api.delete(`/api/salles/${id}`)
}
