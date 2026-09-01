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

function declencherTelechargement(data: Blob, disposition?: string, fallback = 'bulletin.pdf') {
  const match = disposition?.match(/filename="?([^"]+)"?/)
  const nom = match?.[1] ?? fallback
  const url = window.URL.createObjectURL(data)
  const a = document.createElement('a')
  a.href = url
  a.download = nom
  document.body.appendChild(a)
  a.click()
  a.remove()
  window.URL.revokeObjectURL(url)
}

export async function downloadBulletinPdf(id: number): Promise<void> {
  const res = await api.get(`/api/bulletins/pdf/${id}`, { responseType: 'blob' })
  declencherTelechargement(
    res.data as Blob,
    res.headers['content-disposition'],
    `Bulletin_${id}.pdf`,
  )
}

export async function downloadBulletinsClassePdf(idClasse: number, idTrimestre: number): Promise<void> {
  const res = await api.get(`/api/bulletins/classe/${idClasse}/trimestre/${idTrimestre}/pdf`, {
    responseType: 'blob',
  })
  declencherTelechargement(
    res.data as Blob,
    res.headers['content-disposition'],
    `Bulletins_classe_${idClasse}.pdf`,
  )
}
