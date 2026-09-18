import { api } from '@/lib/api'
import type { Etablissement, EtablissementUpdate, EtablissementInfrastructures } from './types'

export type { Etablissement, EtablissementUpdate, EtablissementInfrastructures }

export async function fetchEtablissement(): Promise<Etablissement> {
  const res = await api.get<Etablissement>('/api/etablissement')
  return res.data
}

export async function updateEtablissement(body: EtablissementUpdate): Promise<Etablissement> {
  const res = await api.put<Etablissement>('/api/etablissement', body)
  return res.data
}

export async function uploadLogo(file: File): Promise<string> {
  const fd = new FormData()
  fd.append('file', file)
  const res = await api.post<{ logo: string }>('/api/etablissement/logo', fd, { timeout: 30_000 })
  return res.data.logo
}

export async function uploadSetupLogo(file: File): Promise<string> {
  const fd = new FormData()
  fd.append('file', file)
  const res = await api.post<{ logo: string }>('/api/setup/logo', fd, { timeout: 30_000 })
  return res.data.logo
}

export async function fetchInfrastructures(anneeId?: number): Promise<EtablissementInfrastructures> {
  const res = await api.get<EtablissementInfrastructures>('/api/etablissement/infrastructures', {
    params: anneeId ? { annee_id: anneeId } : {},
  })
  return res.data
}

export async function saveInfrastructures(
  body: Partial<EtablissementInfrastructures> & { id_annee_scolaire?: number | null },
): Promise<EtablissementInfrastructures> {
  const res = await api.put<EtablissementInfrastructures>('/api/etablissement/infrastructures', body)
  return res.data
}
