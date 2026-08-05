import { api } from '@/lib/api'
import type { Seance, SeanceDetail, SeanceCreateInput } from './types'

export type { Seance, SeanceDetail, SeanceCreateInput }

export async function fetchSeances(anneeScolaireId?: number): Promise<SeanceDetail[]> {
  const params: Record<string, number> = {}
  if (anneeScolaireId) params.id_annee_scolaire = anneeScolaireId
  const res = await api.get<SeanceDetail[]>('/api/seances/', { params: { ...params, limit: 500 } })
  return res.data
}

export async function createSeance(body: SeanceCreateInput): Promise<Seance> {
  const res = await api.post<Seance>('/api/seances/', body)
  return res.data
}

export async function updateSeance(id: number, body: SeanceCreateInput): Promise<Seance> {
  const res = await api.put<Seance>(`/api/seances/${id}`, body)
  return res.data
}

export async function deleteSeance(id: number): Promise<void> {
  await api.delete(`/api/seances/${id}`)
}
