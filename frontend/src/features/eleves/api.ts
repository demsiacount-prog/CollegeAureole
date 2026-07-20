import { api } from '@/lib/api'
import type { Eleve, EleveCreateInput, EleveUpdateInput, DossierEleve } from './types'

export async function fetchEleves(): Promise<Eleve[]> {
  const res = await api.get<Eleve[]>('/api/eleves/', { params: { limit: 500 } })
  return res.data
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
