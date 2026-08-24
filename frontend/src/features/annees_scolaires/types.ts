export type { AnneeScolaire } from '@/features/shared/types'

export interface AnneeScolaireCreateInput {
  libelle: string
  date_debut: string
  date_fin: string
  active?: boolean
}
