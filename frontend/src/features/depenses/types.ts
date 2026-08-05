export type CategorieDepense =
  | 'SALAIRES'
  | 'FOURNITURES'
  | 'ENTRETIEN'
  | 'ELECTRICITE'
  | 'EAU'
  | 'COMMUNICATION'
  | 'TRANSPORT'
  | 'ALIMENTATION'
  | 'MATERIEL'
  | 'AUTRE'

export const CATEGORIES: CategorieDepense[] = [
  'SALAIRES', 'FOURNITURES', 'ENTRETIEN', 'ELECTRICITE', 'EAU',
  'COMMUNICATION', 'TRANSPORT', 'ALIMENTATION', 'MATERIEL', 'AUTRE',
]

export const CATEGORIE_LABELS: Record<CategorieDepense, string> = {
  SALAIRES: 'Salaires',
  FOURNITURES: 'Fournitures',
  ENTRETIEN: 'Entretien',
  ELECTRICITE: 'Électricité',
  EAU: 'Eau',
  COMMUNICATION: 'Communication',
  TRANSPORT: 'Transport',
  ALIMENTATION: 'Alimentation',
  MATERIEL: 'Matériel',
  AUTRE: 'Autre',
}

export interface Depense {
  id: number
  code_depense: string | null
  libelle: string
  montant: number
  categorie: CategorieDepense
  date: string
  description: string | null
}

export interface DepenseCreateInput {
  libelle: string
  montant: number
  categorie: CategorieDepense
  date: string
  description?: string | null
}
