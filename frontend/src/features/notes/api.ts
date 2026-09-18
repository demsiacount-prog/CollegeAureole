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
  note_classe: number | null
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
  note_classe?: number | null
  matricule_eleve: string
  id_cours: number
  id_classe: number
  matricule_enseignant: string
  id_trimestre: number | null
}

export interface RegistreNoteLigne {
  id_trimestre: number
  nom: string
  note_comp: number | null
  note_classe: number | null
  moyenne: number | null
  points: number | null
}

export interface RegistreEleve {
  matricule: string
  nom: string
  prenom: string
  lignes: RegistreNoteLigne[]
  moyenne_annuelle: number | null
}

export interface RegistreTrimestre {
  id: number
  nom: string
}

export interface RegistreCours {
  id: number
  nom: string
  coefficient: number
  enseignant: { matricule: string; nom: string; prenom: string } | null
}

export interface RegistreNotes {
  classe: { id: number; niveau: string; nom: string }
  cours: RegistreCours
  annee_libelle: string | null
  bareme: number
  trimestres: RegistreTrimestre[]
  eleves: RegistreEleve[]
}

export async function fetchRegistreNotes(params: {
  classe_id: number
  cours_id: number
  annee_id: number
}): Promise<RegistreNotes> {
  const res = await api.get<RegistreNotes>('/api/notes/registre', { params })
  return res.data
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

export async function patchNote(id: number, payload: Partial<NoteCreatePayload>): Promise<Note> {
  const res = await api.patch<Note>(`/api/notes/${id}`, payload)
  return res.data
}

export interface NoteBulkItem extends NoteCreatePayload {
  id?: number
}

export interface NoteBulkResult {
  notes: Note[]
  creees: number
  modifiees: number
}

export async function saveNotesBulk(items: NoteBulkItem[]): Promise<NoteBulkResult> {
  const res = await api.post<NoteBulkResult>('/api/notes/bulk', { notes: items })
  return res.data
}

export async function deleteNote(id: number): Promise<void> {
  await api.delete(`/api/notes/${id}`)
}
