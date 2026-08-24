import { api } from '@/lib/api'
import type { Eleve } from '@/features/eleves/types'
import type { Classe, Cours } from '@/features/shared/types'
import type { Trimestre } from '@/features/trimestres/types'
import { fetchClasses, fetchClasseDetail } from '@/features/classes/api'
import { fetchTrimestres } from '@/features/trimestres/api'

export { fetchClasses, fetchClasseDetail, fetchTrimestres }

export interface Note {
  id: number
  date: string
  note: number
  matricule_eleve: string
  id_cours: number
  id_classe: number
  matricule_enseignant: string
  id_trimestre: number | null
  created_at: string
  updated_at: string
  eleve: Eleve
  cours: Cours
  classe: Classe
  trimestre: Trimestre | null
}

export interface NoteCreatePayload {
  note: number
  matricule_eleve: string
  id_cours: number
  id_classe: number
  matricule_enseignant: string
  id_trimestre: number | null
}

export async function fetchExistingNotes(params: {
  id_classe: number
  id_cours: number
  id_trimestre: number
}): Promise<Note[]> {
  const res = await api.get<Note[]>('/api/notes/', {
    params: { ...params, limit: 500 },
  })
  return res.data
}

export async function createNote(payload: NoteCreatePayload): Promise<Note> {
  const res = await api.post<Note>('/api/notes/', payload)
  return res.data
}

export async function updateNote(id: number, payload: NoteCreatePayload): Promise<Note> {
  const res = await api.put<Note>(`/api/notes/${id}`, payload)
  return res.data
}

export async function deleteNote(id: number): Promise<void> {
  await api.delete(`/api/notes/${id}`)
}
