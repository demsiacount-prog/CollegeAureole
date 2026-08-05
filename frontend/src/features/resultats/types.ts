// Miroir des modèles définis dans routers/resultats.py (pas de schemas/resultats.py séparé)

export type StatutPassage = 'EN_ATTENTE' | 'ADMIS' | 'RECALE' | 'EXCLU'

export interface EleveResultat {
  inscription_id: number
  matricule: string
  nom: string
  prenom: string
  photo: string | null
  moyenne_annuelle: number | null
  statut_passage: StatutPassage
}

export interface ResultatsClasse {
  classe: { id: number; niveau: string; nom: string }
  niveau_ordre: number | null
  effectif: number
  compteurs: Record<StatutPassage, number>
  eleves: EleveResultat[]
}

export interface DetailRapportAuto {
  matricule: string
  nom: string
  moyenne: number | null
  ancien_statut: StatutPassage
  nouveau_statut: StatutPassage
}

export interface RapportAuto {
  classe: { id: number; niveau: string; nom: string }
  seuil_applique: number
  est_fin_cycle: boolean
  admis: number
  diplomes: number
  recales: number
  exclus_conserves: number
  en_attente: number
  detail: DetailRapportAuto[]
}
