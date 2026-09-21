import { api } from '@/lib/api'
import type { Eleve, EleveCreateInput, EleveUpdateInput, DossierEleve } from './types'

export interface EleveListParams {
  skip?: number
  limit?: number
  q?: string
  classe_id?: number
  statut?: string
  /** Année de consultation : l'effectif, la classe et le statut renvoyés sont
   * ceux de l'inscription de cette année (et non l'état actuel). */
  id_annee_scolaire?: number
}

export async function fetchEleves(params: EleveListParams = {}): Promise<Eleve[]> {
  const res = await api.get<Eleve[]>('/api/eleves/', { params: { limit: 50, ...params } })
  return res.data
}

export async function fetchElevesTotal(q?: string, params: Pick<EleveListParams, 'classe_id' | 'statut' | 'id_annee_scolaire'> = {}): Promise<number> {
  const res = await api.get<{ total: number }>('/api/eleves/compte', {
    params: { ...(q ? { q } : {}), ...params },
  })
  return res.data.total
}

export async function fetchDossierEleve(matricule: string, idAnneeScolaire?: number): Promise<DossierEleve> {
  const res = await api.get<DossierEleve>(`/api/eleves/${matricule}/dossier`, {
    params: idAnneeScolaire ? { id_annee_scolaire: idAnneeScolaire } : {},
  })
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
