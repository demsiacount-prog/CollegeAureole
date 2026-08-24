import { api } from '@/lib/api'
import type { Etablissement, EtablissementUpdate } from './types'

export type { Etablissement, EtablissementUpdate }

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
