import { api } from '@/lib/api'
import type { Eleve } from '@/features/eleves/types'
import type { Classe } from '@/features/shared/types'
import type { Cours } from '@/features/shared/types'
import type { Trimestre } from '@/features/trimestres/types'
import { fetchClasses } from '@/features/classes/api'

export { fetchClasses }

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

export interface ClasseDetail {
  id: number
  niveau: string
  nom: string
  frais_inscription: number
  mensualite: number
  created_at: string
  updated_at: string
  eleves: Eleve[]
  cours: Cours[]
  effectif_actuel: number
}

export async function fetchClasseDetail(id: number): Promise<ClasseDetail> {
  const res = await api.get<ClasseDetail>(`/api/classes/${id}`)
  return res.data
}

export async function fetchTrimestres(anneeScolaireId?: number): Promise<Trimestre[]> {
  const params: Record<string, string | number> = { limit: 500 }
  if (anneeScolaireId) params.annee_scolaire_id = anneeScolaireId
  const res = await api.get<Trimestre[]>('/api/trimestres/', { params })
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
