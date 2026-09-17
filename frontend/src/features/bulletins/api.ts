import { api } from '@/lib/api'
import type {
  Bulletin, BulletinDetailFull, BulletinAnnuel,
  BulletinGenerateClasseInput, BulletinPublierInput,
} from './types'

export type {
  Bulletin, BulletinDetailFull, BulletinAnnuel,
  BulletinGenerateClasseInput, BulletinPublierInput,
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

/** Récupère les octets d'un bulletin (aperçu pdf.js + téléchargement). */
export async function fetchBulletinPdf(id: number): Promise<ArrayBuffer> {
  const res = await api.get(`/api/bulletins/pdf/${id}`, { responseType: 'arraybuffer' })
  return res.data as ArrayBuffer
}

export async function downloadBulletinPdf(id: number): Promise<void> {
  declencherTelechargement(
    new Blob([await fetchBulletinPdf(id)], { type: 'application/pdf' }),
    undefined,
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

export async function fetchBulletinAnnuel(matricule: string, anneeId: number): Promise<BulletinAnnuel> {
  const res = await api.get<BulletinAnnuel>(`/api/bulletins/annuel/${matricule}`, {
    params: { annee_id: anneeId },
  })
  return res.data
}

export async function fetchBulletinAnnuelPdf(matricule: string, anneeId: number): Promise<ArrayBuffer> {
  const res = await api.get(`/api/bulletins/annuel/${matricule}/pdf`, {
    params: { annee_id: anneeId },
    responseType: 'arraybuffer',
  })
  return res.data as ArrayBuffer
}

export async function downloadBulletinAnnuelPdf(matricule: string, anneeId: number): Promise<void> {
  declencherTelechargement(
    new Blob([await fetchBulletinAnnuelPdf(matricule, anneeId)], { type: 'application/pdf' }),
    undefined,
    `Bulletin_annuel_${matricule}.pdf`,
  )
}

export async function downloadBulletinsAnnuelleClassePdf(idClasse: number, anneeId: number): Promise<void> {
  const res = await api.get(`/api/bulletins/annuel/classe/${idClasse}/pdf`, {
    params: { annee_id: anneeId },
    responseType: 'blob',
  })
  declencherTelechargement(
    res.data as Blob,
    res.headers['content-disposition'],
    `Bulletins_annuels_classe_${idClasse}.pdf`,
  )
}
