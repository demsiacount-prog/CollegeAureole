import { api } from '@/lib/api'
import type {
  Bulletin, BulletinDetailFull,
  BulletinGenerateInput, BulletinGenerateClasseInput, BulletinPublierInput,
} from './types'

export type {
  Bulletin, BulletinDetailFull,
  BulletinGenerateInput, BulletinGenerateClasseInput, BulletinPublierInput,
}

export async function fetchBulletins(params?: {
  id_classe?: number
  id_trimestre?: number
  matricule_eleve?: string
}): Promise<Bulletin[]> {
  const res = await api.get<Bulletin[]>('/api/bulletins/', { params: { ...params, limit: 500 } })
  return res.data
}

export async function fetchBulletinDetail(id: number): Promise<BulletinDetailFull> {
  const res = await api.get<BulletinDetailFull>(`/api/bulletins/${id}`)
  return res.data
}

export async function genererBulletin(body: BulletinGenerateInput): Promise<Bulletin> {
  const res = await api.post<Bulletin>('/api/bulletins/generer', body)
  return res.data
}

export async function genererBulletinClasse(body: BulletinGenerateClasseInput): Promise<Bulletin[]> {
  const res = await api.post<Bulletin[]>('/api/bulletins/generer-classe', body)
  return res.data
}

export async function publierBulletins(body: BulletinPublierInput): Promise<Bulletin[]> {
  const res = await api.post<Bulletin[]>('/api/bulletins/publier', body)
  return res.data
}

export async function depublierBulletins(body: BulletinPublierInput): Promise<Bulletin[]> {
  const res = await api.post<Bulletin[]>('/api/bulletins/depublier', body)
  return res.data
}

export async function deleteBulletin(id: number): Promise<void> {
  await api.delete(`/api/bulletins/${id}`)
}
