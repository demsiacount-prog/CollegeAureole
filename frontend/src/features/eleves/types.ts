import type { Tuteur, Classe, AnneeScolaire, Cours, Trimestre, Enseignant, Paiement } from '@/features/shared/types'
import type { Document } from '@/features/documents/types'
import type { BulletinDetail } from '@/features/bulletins/types'

export type { BulletinDetail }

export type StatutEleve = 'actif' | 'inactif'

export interface Eleve {
  matricule: string
  nom: string
  prenom: string
  photo: string | null
  date_de_naissance: string
  lieu_de_naissance: string
  sexe: string
  adresse: string | null
  statut: string
  acte_naissance: boolean
  carnet_sante: boolean
  numero_acte: string | null
  jugement_suppletif: string | null
  date_acte: string | null
  delivre_par: string | null
  nom_pere: string | null
  prenom_pere: string | null
  fonction_pere: string | null
  nom_mere: string | null
  prenom_mere: string | null
  fonction_mere: string | null
  created_at: string
  updated_at: string
  tuteur: Tuteur
  classe: Classe | null
  /** Classe de l'inscription de l'année de consultation (`id_annee_scolaire`),
   * si fournie ; sinon null. */
  classe_annee?: Classe | null
  /** Statut de l'inscription de l'année de consultation, si fournie ; sinon null. */
  statut_annee?: string | null
}

export interface EleveCreateInput {
  nom: string
  prenom: string
  photo?: string | null
  date_de_naissance: string
  lieu_de_naissance: string
  sexe: string
  adresse?: string | null
  statut: string
  tuteur_id: number
  classe_id: number
  annee_scolaire_id?: number | null
  acte_naissance?: boolean
  carnet_sante?: boolean
  numero_acte?: string | null
  jugement_suppletif?: string | null
  date_acte?: string | null
  delivre_par?: string | null
  nom_pere?: string | null
  prenom_pere?: string | null
  fonction_pere?: string | null
  nom_mere?: string | null
  prenom_mere?: string | null
  fonction_mere?: string | null
}

export interface EleveUpdateInput {
  nom?: string
  prenom?: string
  date_de_naissance?: string
  sexe?: string
  lieu_de_naissance?: string
  adresse?: string | null
  classe_id?: number | null
  tuteur_id?: number | null
  statut?: string
  photo?: string | null
  acte_naissance?: boolean
  carnet_sante?: boolean
  numero_acte?: string | null
  jugement_suppletif?: string | null
  date_acte?: string | null
  delivre_par?: string | null
  nom_pere?: string | null
  prenom_pere?: string | null
  fonction_pere?: string | null
  nom_mere?: string | null
  prenom_mere?: string | null
  fonction_mere?: string | null
}

export interface MoyenneTrimestre {
  numero: number
  periode: string
  moyenne: number | null
}

export interface NoteParMatiere {
  matiere: string
  nb_notes: number
  moyenne: number | null
}

export interface InscriptionDetail {
  id: number
  code_inscription: string | null
  matricule_eleve: string
  id_classe: number | null
  id_annee_scolaire: number
  statut: string
  statut_passage: string
  diplome: boolean
  montant_total: number
  date_inscription: string
  date_fin: string | null
  observation: string | null
  credit_disponible: number
  classe: Classe | null
  annee_scolaire: AnneeScolaire | null
  nb_absences: number
  moyenne_annuelle: number | null
  moyennes_par_trimestre: MoyenneTrimestre[]
  paiements: Paiement[]
  montant_paye: number
  reste_a_payer: number
  notes_par_matiere: NoteParMatiere[]
}

export interface NoteEleve {
  id: number
  date: string
  note: number
  matricule_eleve: string
  id_cours: number
  id_classe: number
  matricule_enseignant: string
  created_at: string
  updated_at: string
  cours: Cours
  classe: Classe
  enseignant: Enseignant
  trimestre: Trimestre | null
}

export interface AbsenceEleve {
  id: number
  date_absence: string
  justifiee: boolean
  motif: string | null
  cours: Cours | null
}

export interface BulletinEleve {
  id: number
  matricule_eleve: string
  id_trimestre: number
  id_classe: number
  moyenne_generale: number
  rang: number | null
  appreciation: string | null
  statut: 'BROUILLON' | 'PUBLIE'
  generated_at: string
  published_at: string | null
  created_at: string
  updated_at: string
  details: BulletinDetail[]
}

export interface DossierEleve extends Eleve {
  inscriptions: InscriptionDetail[]
  notes: NoteEleve[]
  absences: AbsenceEleve[]
  bulletins: BulletinEleve[]
  documents: Document[]
  annee_scolaire: AnneeScolaire | null
}
