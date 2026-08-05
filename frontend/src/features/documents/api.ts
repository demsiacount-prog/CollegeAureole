import { api } from '@/lib/api'
import type { Document } from './types'

export async function uploadDocument(matricule: string, typeDocument: string, file: File): Promise<Document> {
  const form = new FormData()
  form.append('matricule_eleve', matricule)
  form.append('type_document', typeDocument)
  form.append('file', file)
  const res = await api.post<Document>('/api/documents/upload', form)
  return res.data
}

export async function fetchDocuments(matricule: string): Promise<Document[]> {
  const res = await api.get<Document[]>(`/api/documents/${matricule}`)
  return res.data
}

export async function deleteDocument(id: number): Promise<void> {
  await api.delete(`/api/documents/${id}`)
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

export async function fetchDocumentBlob(id: number): Promise<Blob> {
  const res = await api.get<Blob>(`/api/documents/file/${id}`, { responseType: 'blob' })
  return res.data
}

export function getDocumentUrl(id: number): string {
  return `${api.defaults.baseURL ?? ''}/api/documents/file/${id}`
}
