import { api } from '@/lib/api'
import type { Depense, DepenseCreateInput } from './types'

export type { Depense, DepenseCreateInput }

export async function fetchDepenses(params?: {
  date_debut?: string
  date_fin?: string
  categorie?: string
  q?: string
  skip?: number
  limit?: number
}): Promise<Depense[]> {
  const res = await api.get<Depense[]>('/api/depenses/', { params: { limit: 500, ...params } })
  return res.data
}

export async function fetchDepensesCompte(params?: {
  date_debut?: string
  date_fin?: string
  categorie?: string
  q?: string
}): Promise<{ total: number; total_montant: number }> {
  const res = await api.get<{ total: number; total_montant: number }>('/api/depenses/compte', { params })
  return res.data
}

export async function createDepense(body: DepenseCreateInput): Promise<Depense> {
  const res = await api.post<Depense>('/api/depenses/', body)
  return res.data
}

export async function updateDepense(id: number, body: Partial<DepenseCreateInput>): Promise<Depense> {
  const res = await api.put<Depense>(`/api/depenses/${id}`, body)
  return res.data
}

export async function deleteDepense(id: number): Promise<void> {
  await api.delete(`/api/depenses/${id}`)
}
