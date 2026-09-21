// Miroir de schemas/cloture.py

import type { StatutPassage } from '@/features/resultats/types'

export type { StatutPassage } from '@/features/resultats/types'

export interface ElevePreview {
  matricule: string
  nom: string
  prenom: string
  classe_id: number | null
  classe_nom: string | null
  niveau: string | null
  statut_passage: StatutPassage
  diplome: boolean
  action_prevue: string
  inscription_id: number
  /** Vrai quand l'élève admis n'a aucune classe du niveau suivant : il ne
   *  pourra pas être réinscrit lors de la clôture. */
  classe_manquante: boolean
}

export interface CompteursPreview {
  ADMIS_PASSAGE: number
  ADMIS_DIPLOME: number
  RECALE_REDOUBLEMENT: number
  EXCLU: number
  EN_ATTENTE: number
}

export interface AnneeInfo {
  id: number
  libelle: string
}

export interface CloturePreview {
  annee_active: AnneeInfo | null
  total_eleves: number
  blocants: number
  peut_executer: boolean
  cloturee: boolean
  compteurs: CompteursPreview
  eleves: ElevePreview[]
  /** Nb d'élèves admis sans classe de destination : à corriger avant clôture. */
  nb_classes_manquantes: number
}

export interface NouvelleAnneeInput {
  libelle: string
  date_debut: string
  date_fin: string
}

export interface EleveCloture {
  matricule: string
  nom: string
  prenom: string
  classe_nom: string | null
  niveau: string | null
}

export interface EleveErreurCloture {
  matricule: string
  nom: string
  prenom: string
  motif: string
}

export interface RapportCloture {
  admis_passage: number
  admis_diplome: number
  recale_redoublement: number
  exclus: number
  total_traites: number
  eleves_admis_passage: EleveCloture[]
  eleves_diplomes: EleveCloture[]
  eleves_redoublants: EleveCloture[]
  eleves_exclus: EleveCloture[]
  /** Élèves NON traités malgré une décision (classe suivante absente, doublon). */
  erreurs: EleveErreurCloture[]
  /** Dérivé de `erreurs`, exposé pour signaler le rattrapage à faire. */
  nb_erreurs: number
}

export interface ClotureExecuterResponse {
  succes: boolean
  ancienne_annee: AnneeInfo
  nouvelle_annee: AnneeInfo
  rapport: RapportCloture
}

export interface ClotureAlerte {
  id: number
  id_annee_scolaire: number
  matricule: string
  nom: string | null
  prenom: string | null
  motif: string
  resolue: boolean
  cree_le: string
  resolue_le: string | null
}

export interface ClotureAlertesReponse {
  nb_en_attente: number
  alertes: ClotureAlerte[]
}
