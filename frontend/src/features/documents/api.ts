import { api } from '@/lib/api'
import type {
  Document,
  DocumentAvecEntite,
  DocumentCategorieKey,
  DocumentRead,
  EntiteDocument,
} from './types'

/** Clé de cache React Query partagée entre `useDocuments` et l'onglet. */
export function documentsQueryKey(entiteType: EntiteDocument, entiteId: string) {
  return ['documents', entiteType, entiteId] as const
}

// ── API générique (§46) ──────────────────────────────────────────────────────
export async function fetchDocumentsByEntite(
  entiteType: EntiteDocument,
  entiteId: string,
): Promise<DocumentRead[]> {
  const res = await api.get<DocumentRead[]>('/api/documents/', {
    params: { entite_type: entiteType, entite_id: entiteId },
  })
  return res.data
}

export interface UploadDocumentParams {
  entiteType: EntiteDocument
  entiteId: string
  fichier: File
  nom?: string
  categorie?: DocumentCategorieKey
}

export async function uploadDocumentGenerique(params: UploadDocumentParams): Promise<DocumentRead> {
  const form = new FormData()
  form.append('entite_type', params.entiteType)
  form.append('entite_id', params.entiteId)
  form.append('fichier', params.fichier)
  if (params.nom) form.append('nom', params.nom)
  if (params.categorie) form.append('categorie', params.categorie)
  const res = await api.post<DocumentRead>('/api/documents/', form)
  return res.data
}

export async function modifierDocument(
  id: number,
  data: { nom?: string; categorie?: DocumentCategorieKey },
): Promise<DocumentRead> {
  const res = await api.patch<DocumentRead>(`/api/documents/${id}`, data)
  return res.data
}

export async function deleteDocument(id: number): Promise<void> {
  await api.delete(`/api/documents/${id}`)
}

/** Récupère le contenu binaire d'un document (téléchargement / aperçu). */
export async function fetchDocumentBlob(id: number): Promise<Blob> {
  const res = await api.get<Blob>(`/api/documents/${id}/fichier`, { responseType: 'blob' })
  return res.data
}

export function downloadBlob(blob: Blob, filename: string): void {
  // Un <a href> vers l'API ne porterait pas l'en-tête Authorization (le
  // navigateur envoie une requête brute → 401). On récupère le contenu via
  // axios (authentifié) puis on déclenche le téléchargement localement.
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}

export async function downloadDocument(id: number, filename: string): Promise<void> {
  downloadBlob(await fetchDocumentBlob(id), filename)
}

// ── Uploads rétro-compat (par entité, champ type_document) ──────────────────
export async function uploadDocument(matricule: string, typeDocument: string, file: File): Promise<Document> {
  const form = new FormData()
  form.append('matricule_eleve', matricule)
  form.append('type_document', typeDocument)
  form.append('file', file)
  const res = await api.post<Document>('/api/documents/upload', form)
  return res.data
}

export async function uploadDocumentEnseignant(matricule: string, typeDocument: string, file: File): Promise<Document> {
  const form = new FormData()
  form.append('matricule_enseignant', matricule)
  form.append('type_document', typeDocument)
  form.append('file', file)
  const res = await api.post<Document>('/api/documents/enseignant/upload', form)
  return res.data
}

export async function fetchDocumentsEnseignant(matricule: string): Promise<Document[]> {
  const res = await api.get<Document[]>(`/api/documents/enseignant/${matricule}`)
  return res.data
}

export async function uploadDocumentTuteur(codeTuteur: string, typeDocument: string, file: File): Promise<Document> {
  const form = new FormData()
  form.append('code_tuteur', codeTuteur)
  form.append('type_document', typeDocument)
  form.append('file', file)
  const res = await api.post<Document>('/api/documents/tuteur/upload', form)
  return res.data
}

export async function fetchDocumentsTuteur(codeTuteur: string): Promise<Document[]> {
  const res = await api.get<Document[]>(`/api/documents/tuteur/${codeTuteur}`)
  return res.data
}

export async function fetchTousDocuments(): Promise<DocumentAvecEntite[]> {
  const res = await api.get<DocumentAvecEntite[]>('/api/documents/')
  return res.data
}