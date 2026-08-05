import { api } from '@/lib/api'
import type { Paiement, PaiementCreateInput, PaiementResult, Echeance, Relance } from './types'

export type { Paiement, PaiementCreateInput, PaiementResult, Echeance, Relance }

export async function fetchPaiements(params?: {
  id_inscription?: number
  matricule_eleve?: string
  date_debut?: string
  date_fin?: string
  q?: string
  skip?: number
  limit?: number
}): Promise<Paiement[]> {
  const res = await api.get<Paiement[]>('/api/paiements/', { params: { limit: 500, ...params } })
  return res.data
}

export async function fetchPaiementsTotal(params?: {
  id_inscription?: number
  matricule_eleve?: string
  date_debut?: string
  date_fin?: string
  q?: string
}): Promise<number> {
  const res = await api.get<{ total: number }>('/api/paiements/compte', { params })
  return res.data.total
}

export async function fetchRelances(): Promise<Relance[]> {
  const res = await api.get<Relance[]>('/api/paiements/relances')
  return res.data
}

export async function fetchEcheances(idInscription: number): Promise<Echeance[]> {
  const res = await api.get<Echeance[]>(`/api/paiements/echeances/${idInscription}`)
  return res.data
}

export async function createPaiement(body: PaiementCreateInput): Promise<PaiementResult> {
  const res = await api.post<PaiementResult>('/api/paiements/', body)
  return res.data
}

export async function deletePaiement(id: number): Promise<void> {
  await api.delete(`/api/paiements/${id}`)
}
