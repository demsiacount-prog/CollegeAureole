import { api } from '@/lib/api'
import type { Inscription, InscriptionDetail, InscriptionCreateInput } from './types'
import type { TuteurCreateInput } from '@/features/tuteurs/api'
import type { EleveCreateInput } from '@/features/eleves/types'

export type { Inscription, InscriptionDetail, InscriptionCreateInput }

export async function fetchInscriptions(params?: {
  matricule_eleve?: string
  id_classe?: number
  id_annee_scolaire?: number
  statut?: string
  q?: string
  skip?: number
  limit?: number
}): Promise<Inscription[]> {
  const res = await api.get<Inscription[]>('/api/inscriptions/', { params: { limit: 500, ...params } })
  return res.data
}

export async function fetchInscriptionsTotal(params?: {
  matricule_eleve?: string
  id_classe?: number
  id_annee_scolaire?: number
  statut?: string
  q?: string
}): Promise<number> {
  const res = await api.get<{ total: number }>('/api/inscriptions/compte', { params })
  return res.data.total
}

export async function fetchInscriptionDetail(id: number): Promise<InscriptionDetail> {
  const res = await api.get<InscriptionDetail>(`/api/inscriptions/${id}`)
  return res.data
}

export async function createInscription(body: InscriptionCreateInput): Promise<Inscription> {
  const res = await api.post<Inscription>('/api/inscriptions/', body)
  return res.data
}

export async function deleteInscription(id: number): Promise<void> {
  await api.delete(`/api/inscriptions/${id}`)
}

export interface DossierCompletInput {
  tuteur?: TuteurCreateInput & { profession?: string }
  tuteur_id?: number
  eleve: Omit<EleveCreateInput, 'tuteur_id' | 'classe_id'>
  classe_id: number | null
  id_annee_scolaire: number
  observation?: string | null
}

export async function creerDossierComplet(input: DossierCompletInput): Promise<Inscription> {
  const res = await api.post<Inscription>('/api/inscriptions/dossier-complet', {
    tuteur_id: input.tuteur_id ?? undefined,
    tuteur: input.tuteur ?? undefined,
    eleve: input.eleve,
    classe_id: input.classe_id,
    id_annee_scolaire: input.id_annee_scolaire,
    observation: input.observation ?? null,
  })
  return res.data
}
