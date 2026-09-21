import { api } from '@/lib/api'

export interface SauvegardeServeur {
  nom: string
  taille_octets: number
  cree_le: string
}

export interface ImportResultat {
  message: string
  lignes_importees: number
  sauvegarde_avant_restauration: string
}

// Valeur d'armement exigée par le backend pour toute restauration destructrice.
const CONFIRM_TOKEN = 'RESTAURATION-DONNEES'

export async function fetchSauvegardesServeur(): Promise<SauvegardeServeur[]> {
  const res = await api.get<{ sauvegardes: SauvegardeServeur[] }>('/api/import-export/sauvegardes')
  return res.data.sauvegardes
}

export async function creerSauvegardeServeur(): Promise<string> {
  const res = await api.post<{ sauvegarde: string }>('/api/import-export/sauvegarde')
  return res.data.sauvegarde
}

function declencherTelechargement(data: Blob, disposition?: string, fallback = 'collegeaureole_sauvegarde.zip') {
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

export async function telechargerSauvegardeComplete(): Promise<void> {
  const res = await api.get('/api/import-export/export/complet', { responseType: 'blob' })
  declencherTelechargement(res.data as Blob, res.headers['content-disposition'])
}

export async function telechargerExportExcel(): Promise<void> {
  const res = await api.get('/api/import-export/export', { responseType: 'blob' })
  declencherTelechargement(res.data as Blob, res.headers['content-disposition'], 'collegeaureole_export.xlsx')
}

export async function importerSauvegarde(fichier: File): Promise<ImportResultat> {
  const fd = new FormData()
  fd.append('fichier', fichier)
  fd.append('remplacer', 'true')
  const res = await api.post<ImportResultat>('/api/import-export/import', fd, {
    headers: { 'X-Confirm': CONFIRM_TOKEN },
  })
  return res.data
}

export function formaterTaille(octets: number): string {
  if (octets < 1024) return `${octets} o`
  const unites = ['Ko', 'Mo', 'Go']
  let valeur = octets / 1024
  let i = 0
  while (valeur >= 1024 && i < unites.length - 1) {
    valeur /= 1024
    i += 1
  }
  return `${valeur.toFixed(1)} ${unites[i]}`
}