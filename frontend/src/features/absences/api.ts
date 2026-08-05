import { api } from '@/lib/api'
import type { Absence, AlerteAbsence, AbsenceCreateInput, AbsenceJustifierInput } from './types'

export type { Absence, AlerteAbsence, AbsenceCreateInput, AbsenceJustifierInput }

export async function fetchAbsences(params?: {
  classe_id?: number
  matricule_eleve?: string
  id_cours?: number
  date_debut?: string
  date_fin?: string
  justifiee?: boolean
  q?: string
  skip?: number
  limit?: number
}): Promise<Absence[]> {
  const res = await api.get<Absence[]>('/api/absences/', { params: { limit: 500, ...params } })
  return res.data
}

export async function fetchAbsencesTotal(params?: {
  classe_id?: number
  matricule_eleve?: string
  id_cours?: number
  date_debut?: string
  date_fin?: string
  justifiee?: boolean
  q?: string
}): Promise<number> {
  const res = await api.get<{ total: number }>('/api/absences/compte', { params })
  return res.data.total
}

export async function fetchAlertesAbsences(seuil = 3): Promise<AlerteAbsence[]> {
  const res = await api.get<AlerteAbsence[]>('/api/absences/alertes', { params: { seuil } })
  return res.data
}

export async function createAbsence(body: AbsenceCreateInput): Promise<Absence> {
  const res = await api.post<Absence>('/api/absences/', body)
  return res.data
}

export async function justifierAbsence(id: number, body: AbsenceJustifierInput): Promise<Absence> {
  const res = await api.patch<Absence>(`/api/absences/${id}/justifier`, body)
  return res.data
}
