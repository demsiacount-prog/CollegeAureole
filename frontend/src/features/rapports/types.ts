// Types miroir des schémas Pydantic de backend/schemas/rapports.py.

export interface EleveMoyenne {
  inscription_id: number
  matricule: string
  nom: string
  prenom: string
  moyenne_annuelle: number | null
  rang: number | null
  statut_passage: string
}

export interface ClasseMoyennes {
  id_classe: number
  niveau: string
  nom: string
  bareme: number
  effectif: number
  moyenne_classe: number | null
  eleves: EleveMoyenne[]
}

export interface RapportMoyennes {
  annee_label: string
  classes: ClasseMoyennes[]
}

export interface EleveProposition {
  inscription_id: number
  matricule: string
  nom: string
  prenom: string
  moyenne_annuelle: number | null
  statut_actuel: string
  proposition: string
}

export interface ClasseProposition {
  id_classe: number
  niveau: string
  nom: string
  bareme: number
  seuil: number
  est_fin_cycle: boolean
  effectif: number
  admis: number
  recales: number
  en_attente: number
  exclus: number
  eleves: EleveProposition[]
}

export interface PropositionPassage {
  annee_label: string
  classes: ClasseProposition[]
}

export interface RapportsParams {
  classeId?: number
  anneeId?: number
}

export interface MoyenneTrimestre {
  periode: string
  moyenne: number | null
}

export interface NoteParMatiere {
  matiere: string
  nb_notes: number
  moyenne: number | null
}

export interface ParcoursAnnee {
  annee_label: string
  classe: string | null
  niveau: string | null
  statut_passage: string
  moyenne_annuelle: number | null
}

export interface FicheSuiviPassage {
  niveau: string
  passage: number
  label: string
  annee_label: string | null
  statut_passage: string | null
  moyenne_annuelle: number | null
  effectue: boolean
  moyennes: (number | null)[]
}

export interface FicheSuiviLigne {
  matiere: string
  valeurs: (number | null)[]
  tendance: string | null
}

export interface FicheSuivi {
  matricule: string
  nom: string
  prenom: string
  date_de_naissance: string | null
  lieu_de_naissance: string
  sexe: string
  adresse: string | null
  pere: string | null
  mere: string | null
  niveau: string | null
  classe: string | null
  bareme: number
  est_jardin: boolean
  transfert: boolean
  annee_label: string
  moyenne_annuelle: number | null
  rang: number | null
  effectif: number | null
  moyennes_trimestres: MoyenneTrimestre[]
  notes_par_matiere: NoteParMatiere[]
  colonnes: FicheSuiviPassage[]
  lignes: FicheSuiviLigne[]
  orientation: string | null
  remarques: string[]
  fois_x: number
  nb_absences: number
  nb_absences_justifiees: number
  nb_absences_injustifiees: number
  parcours: ParcoursAnnee[]
}

// ─── Rapport succinct de rentrée (doc5) ────────────────────────────────────────

export interface RapportRentreeClasse {
  annee_etude: string
  groupes: number
  garcons: number
  filles: number
  total: number
  redoublants_g: number
  redoublants_f: number
  redoublants_total: number
}

export interface RapportRentreeCycle {
  cycle: string
  fe: number
  fc: number
  ce: number
  cc: number
  autres: number
  em: number
  total: number
}

export interface RapportRentree {
  annee_label: string
  ecole: string
  village_quartier: string | null
  commune: string | null
  cap: string | null
  cercle: string | null
  ae: string | null
  cycles: string[]
  statuts: string[]
  types_modes: string[]
  classes: RapportRentreeClasse[]
  total_garcons: number
  total_filles: number
  total_general: number
  total_redoublants_g: number
  total_redoublants_f: number
  total_redoublants: number
  premiers_cycle: RapportRentreeCycle
  second_cycle: RapportRentreeCycle
  nb_salles_1er: number
  nb_salles_2nd: number
}

// ─── Classement des élèves (doc1) ──────────────────────────────────────────────

export interface ClassementEleve {
  inscription_id: number
  matricule: string
  nom: string
  prenom: string
  moyenne_annuelle: number | null
  rang: number | null
  observation: string | null
}

export interface ClassementClasse {
  id_classe: number
  niveau: string
  nom: string
  bareme: number
  effectif: number
  moyenne_classe: number | null
  eleves: ClassementEleve[]
}

export interface ClassementResponse {
  annee_label: string
  classes: ClassementClasse[]
}

// ─── Fiche de renseignements de rentrée, 2nd cycle (doc6) ─────────────────────

export interface FicheRenseignementsCellule {
  rc: number
  garcons: number
  filles: number
  total: number
}

export interface FicheRenseignementsLigne {
  libelle: string
  sept: FicheRenseignementsCellule
  huit: FicheRenseignementsCellule
  neuf: FicheRenseignementsCellule
  total: FicheRenseignementsCellule
}

export interface FicheRenseignementsPersonnel {
  prenom: string
  nom: string
  genre: string | null
  nina: string | null
  date_naissance: string | null
  categorie: string | null
  classe: string | null
  echelon: string | null
  fonction: string | null
  sf_nombre_enfants: string | null
  date_contrat: string | null
  classe_tenue: string | null
  dernier_poste: string | null
  date_arrivee_cap: string | null
  observations: string | null
  diplome: string | null
}

export interface FicheRenseignementsResponse {
  annee_label: string
  academie: string | null
  cap: string | null
  ecole: string
  telephone: string | null
  dirigee_par: string | null
  effectifs: FicheRenseignementsLigne[]
  personnel: FicheRenseignementsPersonnel[]
}

// ─── Fiche de renseignements de rentrée, 1er cycle (doc5) ─────────────────────

export interface FicheRensPCLigne {
  libelle: string
  annee_1: FicheRenseignementsCellule
  annee_2: FicheRenseignementsCellule
  annee_3: FicheRenseignementsCellule
  annee_4: FicheRenseignementsCellule
  annee_5: FicheRenseignementsCellule
  annee_6: FicheRenseignementsCellule
  total: FicheRenseignementsCellule
}

export interface FicheRensPCPersonnel {
  prenom: string
  nom: string
  numero_mle: string | null
  date_naissance: string | null
  grade: string | null
  sf: string | null
  nbre_enfants: string | null
  fonction: string | null
  date_recrutement: string | null
  date_titularisation: string | null
  date_dernier_avancement: string | null
  dernier_poste: string | null
  date_arrivee_cap: string | null
  classe_tenue: string | null
  observations: string | null
  diplome: string | null
}

export interface FicheRenseignementsPremierCycleResponse {
  annee_label: string
  cap: string | null
  commune: string | null
  ecole: string
  village_quartier: string | null
  dirige_par: string | null
  telephone: string | null
  effectifs: FicheRensPCLigne[]
  personnel_admin: FicheRensPCPersonnel[]
  personnel_enseignant: FicheRensPCPersonnel[]
}

// ─── Fiche de notes mensuelle / de composition, élève (doc7 + doc3) ──────────

export interface FicheNotesCompoMatiere {
  matiere: string
  note: number | null
  coef: number | null
  observation: string | null
}

export interface FicheNotesCompoResponse {
  matricule: string
  nom: string
  prenom: string
  niveau: string | null
  classe: string | null
  bareme: number
  est_jardin: boolean
  annee_label: string
  mois: string | null
  matieres: FicheNotesCompoMatiere[]
  total_notes: number | null
  moyenne: number | null
  rang: number | null
  effectif: number
  moyenne_annuelle: number | null
  rang_annuel: number | null
  effectif_annuel: number
}

// (doc8 — carnet scolaire supprimé : l'affichage se fait par les bulletins)