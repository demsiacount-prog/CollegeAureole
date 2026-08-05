export type TypePeriode = 'TRIMESTRE' | 'COMPOSITION'

export const TYPE_PERIODE_OPTIONS: { value: TypePeriode; label: string }[] = [
  { value: 'TRIMESTRE', label: 'Trimestre (7e – 9e année)' },
  { value: 'COMPOSITION', label: 'Composition (1e – 6e année)' },
]

export const TYPE_PERIODE_LABELS: Record<TypePeriode, string> = {
  TRIMESTRE: 'Trimestre',
  COMPOSITION: 'Composition',
}

export interface Trimestre {
  id: number
  nom: string
  type: TypePeriode
  date_debut: string
  date_fin: string
  verrouille: boolean
  annee_scolaire_id: number
  created_at: string
  updated_at: string
}

export interface TrimestreCreateInput {
  nom: string
  type: TypePeriode
  date_debut: string
  date_fin: string
  annee_scolaire_id: number
}
