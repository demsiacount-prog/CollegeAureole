import { api } from '@/lib/api'
import type { Cours, CoursCreateInput } from './types'

export type { Cours, CoursCreateInput }

export async function fetchCours(): Promise<Cours[]> {
  const res = await api.get<Cours[]>('/api/cours/', { params: { limit: 500 } })
  return res.data
}

export async function createCours(body: CoursCreateInput): Promise<Cours> {
  const res = await api.post<Cours>('/api/cours/', body)
  return res.data
}

export async function updateCours(id: number, body: CoursCreateInput): Promise<Cours> {
  const res = await api.put<Cours>(`/api/cours/${id}`, body)
  return res.data
}

export async function deleteCours(id: number): Promise<void> {
  await api.delete(`/api/cours/${id}`)
}


