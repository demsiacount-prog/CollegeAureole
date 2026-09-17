// ── Types backend (miroir des schémas Pydantic) ─────────────────────────────
export interface Document {
  id: number
  matricule_eleve: string | null
  matricule_enseignant: string | null
  code_tuteur: string | null
  type_document: string
  filename: string
  taille: number | null
  mime_type: string | null
  uploaded_at: string
}

export type DocumentCategorie = 'eleve' | 'enseignant' | 'tuteur'

export interface DocumentAvecEntite extends Document {
  categorie: DocumentCategorie
  entite_label: string
}

// ── API générique documents (§46) ────────────────────────────────────────────
export type EntiteDocument = 'eleve' | 'enseignant' | 'tuteur'

/** Regroupement Type K — l'ordre d'affichage des sections suit cet ordre. */
export type DocumentCategorieKey =
  | 'identite'
  | 'photo'
  | 'naissance'
  | 'scolaire'
  | 'medical'
  | 'administratif'
  | 'autre'

/** Contrat REST générique des documents (miroir de `DocumentRead` §46). */
export interface DocumentRead {
  id: number
  nom: string
  categorie: DocumentCategorieKey
  entite_type: EntiteDocument | null
  entite_id: string | null
  nom_fichier_original: string | null
  type_mime: string | null
  taille_octets: number | null
  created_at: string
  url_preview: string
  url_download: string
  // Alias rétro-compat (routes historiques, embeds de dossier).
  matricule_eleve?: string | null
  matricule_enseignant?: string | null
  code_tuteur?: string | null
  type_document?: string | null
  filename: string
  taille?: number | null
  mime_type?: string | null
  uploaded_at?: string | null
  entite_label?: string | null
}

// ── Modèle UI (design system §22–§27) ───────────────────────────────────────
export type FileType = 'pdf' | 'word' | 'sheet' | 'image' | 'other'
export type FileTypeSize = 'xs' | 'sm' | 'md' | 'lg'

export type DocumentStatus = 'brouillon' | 'en_attente' | 'valide' | 'archive' | 'erreur'

/** Représentation normalisée d'un document côté interface (design §23). */
export interface UiDocument {
  id: number
  name: string
  filename: string
  type: FileType
  status: DocumentStatus
  sizeBytes?: number
  mimeType?: string
  createdAt: Date
  /** Entité associée (élève/enseignant/tuteur). */
  entityLabel?: string
  entityType?: DocumentCategorie
  entityHref?: string
}