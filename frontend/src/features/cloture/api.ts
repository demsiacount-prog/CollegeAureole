import { api } from '@/lib/api'
import type { ClotureExecuterResponse, CloturePreview, NouvelleAnneeInput } from './types'

export async function fetchCloturePreview(): Promise<CloturePreview> {
  const res = await api.get<CloturePreview>('/api/cloture/preview')
  return res.data
}

export async function executerCloture(nouvelleAnnee: NouvelleAnneeInput): Promise<ClotureExecuterResponse> {
  const res = await api.post<ClotureExecuterResponse>('/api/cloture/executer', { nouvelle_annee: nouvelleAnnee })
  return res.data
}
