import { api } from '@/lib/api'
import type { Paiement, PaiementCreateInput, PaiementUpdateInput, PaiementResult, Echeance, Remise, RemiseCreateInput, PaiementGroupeInput, PaiementGroupeResult, PaiementStats } from './types'

export type { Paiement, PaiementCreateInput, PaiementUpdateInput, PaiementResult, Echeance, Remise, RemiseCreateInput, PaiementGroupeInput, PaiementGroupeResult, PaiementStats }

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

export async function fetchPaiementStats(): Promise<PaiementStats> {
  const res = await api.get<PaiementStats>('/api/paiements/stats')
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

export async function updatePaiement(id: number, body: PaiementUpdateInput): Promise<Paiement> {
  const res = await api.put<Paiement>(`/api/paiements/${id}`, body)
  return res.data
}

export async function deletePaiement(id: number): Promise<void> {
  await api.delete(`/api/paiements/${id}`)
}

export async function fetchRecuPaiement(id: number): Promise<Blob> {
  const res = await api.get<Blob>(`/api/paiements/${id}/recu`, { responseType: 'blob' })
  return res.data
}

export async function fetchRemises(idEcheance: number): Promise<Remise[]> {
  const res = await api.get<Remise[]>(`/api/paiements/echeances/${idEcheance}/remises`)
  return res.data
}

export async function createRemise(idEcheance: number, body: RemiseCreateInput): Promise<Remise> {
  const res = await api.post<Remise>(`/api/paiements/echeances/${idEcheance}/remises`, body)
  return res.data
}

export async function deleteRemise(idRemise: number): Promise<void> {
  await api.delete(`/api/paiements/remises/${idRemise}`)
}

export async function createPaiementGroupe(body: PaiementGroupeInput): Promise<PaiementGroupeResult> {
  const res = await api.post<PaiementGroupeResult>('/api/paiements/groupes', body)
  return res.data
}
