import { api } from '@/lib/api'
import type { Classe } from '@/features/shared/types'
import type { Eleve } from '@/features/eleves/types'
import type { Cours } from '@/features/shared/types'

export interface ClasseCreateInput {
  niveau: string
  nom: string
  frais_inscription?: number
  mensualite?: number
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

export async function fetchClasses(): Promise<Classe[]> {
  const res = await api.get<Classe[]>('/api/classes/', { params: { limit: 500 } })
  return res.data
}

export async function fetchClasseDetail(id: number): Promise<ClasseDetail> {
  const res = await api.get<ClasseDetail>(`/api/classes/${id}`)
  return res.data
}

export async function createClasse(body: ClasseCreateInput): Promise<Classe> {
  const res = await api.post<Classe>('/api/classes/', body)
  return res.data
}

export async function updateClasse(id: number, body: ClasseCreateInput): Promise<Classe> {
  const res = await api.put<Classe>(`/api/classes/${id}`, body)
  return res.data
}

export async function deleteClasse(id: number): Promise<void> {
  await api.delete(`/api/classes/${id}`)
}
