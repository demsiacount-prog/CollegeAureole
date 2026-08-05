import type { Classe, Enseignant } from '@/features/shared/types'

export interface AffectationCoursClasse {
  id_classe: number
  coefficient: number
}

export interface AffectationCoursClasseResponse {
  id_classe: number
  coefficient: number
  created_at: string
  updated_at: string
}

export interface Cours {
  id: number
  code_cours: string | null
  nom: string
  description: string
  volume_horaire: number
  matricule_enseignant: string | null
  created_at: string
  updated_at: string
  classes: Classe[]
  coefficients: AffectationCoursClasseResponse[]
  enseignant: Enseignant | null
}

export interface CoursCreateInput {
  nom: string
  description: string
  volume_horaire: number
  matricule_enseignant?: string | null
  affectations: AffectationCoursClasse[]
}
