import { api } from '@/lib/api'
import { createTuteur } from '@/features/tuteurs/api'
import { createEleve } from '@/features/eleves/api'
import type { Inscription, InscriptionDetail, InscriptionCreateInput } from './types'
import type { TuteurCreateInput } from '@/features/tuteurs/api'
import type { EleveCreateInput } from '@/features/eleves/types'

export type { Inscription, InscriptionDetail, InscriptionCreateInput }

export async function fetchInscriptions(params?: {
  matricule_eleve?: string
  id_classe?: number
  id_annee_scolaire?: number
  statut?: string
  q?: string
  skip?: number
  limit?: number
}): Promise<Inscription[]> {
  const res = await api.get<Inscription[]>('/api/inscriptions/', { params: { limit: 500, ...params } })
  return res.data
}

export async function fetchInscriptionsTotal(params?: {
  matricule_eleve?: string
  id_classe?: number
  id_annee_scolaire?: number
  statut?: string
  q?: string
}): Promise<number> {
  const res = await api.get<{ total: number }>('/api/inscriptions/compte', { params })
  return res.data.total
}

export async function fetchInscriptionDetail(id: number): Promise<InscriptionDetail> {
  const res = await api.get<InscriptionDetail>(`/api/inscriptions/${id}`)
  return res.data
}

export async function createInscription(body: InscriptionCreateInput): Promise<Inscription> {
  const res = await api.post<Inscription>('/api/inscriptions/', body)
  return res.data
}

export async function deleteInscription(id: number): Promise<void> {
  await api.delete(`/api/inscriptions/${id}`)
}

export interface DossierCompletInput {
  tuteur?: TuteurCreateInput & { profession?: string }
  tuteur_id?: number
  eleve: Omit<EleveCreateInput, 'tuteur_id' | 'classe_id'>
  classe_id: number | null
  id_annee_scolaire: number
  observation?: string | null
}

export async function creerDossierComplet(input: DossierCompletInput): Promise<Inscription> {
  let tuteurId: number
  if (input.tuteur_id) {
    tuteurId = input.tuteur_id
  } else if (input.tuteur) {
    const t = await createTuteur({
      nom: input.tuteur.nom,
      prenom: input.tuteur.prenom,
      telephone: input.tuteur.telephone,
      email: input.tuteur.email,
      adresse: input.tuteur.adresse,
      profession: input.tuteur.profession ?? '',
    })
    tuteurId = t.id
  } else {
    throw new Error("Aucun tuteur fourni")
  }

  const e = await createEleve({
    nom: input.eleve.nom,
    prenom: input.eleve.prenom,
    date_de_naissance: input.eleve.date_de_naissance,
    lieu_de_naissance: input.eleve.lieu_de_naissance,
    sexe: input.eleve.sexe,
    adresse: input.eleve.adresse ?? null,
    statut: 'actif',
    tuteur_id: tuteurId,
    classe_id: input.classe_id,
    annee_scolaire_id: input.id_annee_scolaire,
  })

  return createInscription({
    matricule_eleve: e.matricule,
    id_classe: input.classe_id,
    id_annee_scolaire: input.id_annee_scolaire,
    observation: input.observation ?? null,
  })
}
