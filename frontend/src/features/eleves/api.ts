import { api } from '@/lib/api'
import type { Eleve, EleveCreateInput, EleveUpdateInput, DossierEleve } from './types'

export interface EleveListParams {
  skip?: number
  limit?: number
  q?: string
}

export async function fetchEleves(params: EleveListParams = {}): Promise<Eleve[]> {
  const res = await api.get<Eleve[]>('/api/eleves/', { params: { limit: 50, ...params } })
  return res.data
}

export async function fetchElevesTotal(q?: string): Promise<number> {
  const res = await api.get<{ total: number }>('/api/eleves/compte', {
    params: q ? { q } : undefined,
  })
  return res.data.total
}

export async function fetchEleve(matricule: string): Promise<Eleve> {
  const res = await api.get<Eleve>(`/api/eleves/${matricule}`)
  return res.data
}

export async function fetchDossierEleve(matricule: string): Promise<DossierEleve> {
  const res = await api.get<DossierEleve>(`/api/eleves/${matricule}/dossier`)
  return res.data
}

export async function createEleve(payload: EleveCreateInput): Promise<Eleve> {
  const res = await api.post<Eleve>('/api/eleves/', payload)
  return res.data
}

export async function updateEleve(matricule: string, payload: EleveUpdateInput): Promise<Eleve> {
  const res = await api.put<Eleve>(`/api/eleves/${matricule}`, payload)
  return res.data
}

export async function activerEleve(matricule: string): Promise<Eleve> {
  const res = await api.patch<Eleve>(`/api/eleves/${matricule}/activer`)
  return res.data
}

export async function desactiverEleve(matricule: string): Promise<Eleve> {
  const res = await api.patch<Eleve>(`/api/eleves/${matricule}/desactiver`)
  return res.data
}
