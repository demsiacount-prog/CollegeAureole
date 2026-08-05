import { api } from '@/lib/api'
import type { RapportAuto, ResultatsClasse, StatutPassage } from './types'

export async function fetchResultatsClasse(idClasse: number): Promise<ResultatsClasse> {
  const res = await api.get<ResultatsClasse>(`/api/resultats/${idClasse}`)
  return res.data
}

export async function calculerAutomatiquement(idClasse: number): Promise<RapportAuto> {
  const res = await api.post<RapportAuto>(`/api/resultats/${idClasse}/calcul-auto`)
  return res.data
}

export async function modifierStatutPassage(inscriptionId: number, statut: StatutPassage) {
  const res = await api.put(`/api/resultats/statut/${inscriptionId}`, { statut })
  return res.data
}
