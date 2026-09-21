import { api } from '@/lib/api'
import type {
  ClotureAlerte,
  ClotureAlertesReponse,
  ClotureExecuterResponse,
  CloturePreview,
  NouvelleAnneeInput,
} from './types'

export async function fetchCloturePreview(): Promise<CloturePreview> {
  const res = await api.get<CloturePreview>('/api/cloture/preview')
  return res.data
}

export async function executerCloture(nouvelleAnnee: NouvelleAnneeInput): Promise<ClotureExecuterResponse> {
  const res = await api.post<ClotureExecuterResponse>('/api/cloture/executer', { nouvelle_annee: nouvelleAnnee })
  return res.data
}

export async function fetchClotureAlertes(): Promise<ClotureAlertesReponse> {
  const res = await api.get<ClotureAlertesReponse>('/api/cloture/alertes')
  return res.data
}

export async function resoudreAlerteCloture(id: number): Promise<ClotureAlerte> {
  const res = await api.post<ClotureAlerte>(`/api/cloture/alertes/${id}/resoudre`)
  return res.data
}