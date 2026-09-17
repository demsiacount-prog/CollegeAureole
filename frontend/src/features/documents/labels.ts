import type { BadgeTone } from '@/components/ui/Badge'
import type {
  Document,
  DocumentCategorie,
  DocumentCategorieKey,
  DocumentRead,
  DocumentStatus,
  FileType,
  UiDocument,
} from './types'

// ── Catégories Type K (design system v6.0 § « Gestion Documentaire ») ───────
export const DOC_CATEGORIES: Record<DocumentCategorieKey, string> = {
  identite: "Pièces d'identité",
  photo: 'Photos',
  naissance: 'Actes de naissance',
  scolaire: 'Documents scolaires',
  medical: 'Documents médicaux',
  administratif: 'Administratif',
  autre: 'Autres',
}

export const DOC_CATEGORY_ORDER: DocumentCategorieKey[] = [
  'identite',
  'photo',
  'naissance',
  'scolaire',
  'medical',
  'administratif',
  'autre',
]

// ── Types de document par entité (déjà utilisés par les onglets) ───────────
export const ELEVE_DOCS_LABELS: Record<string, string> = {
  acte_naissance: 'Acte de naissance',
  carnet_sante: 'Carnet de santé',
}

export const ENSEIGNANT_DOCS_LABELS: Record<string, string> = {
  piece_identite: "Pièce d'identité",
  cv: 'Curriculum vitae',
  diplome: 'Diplômes',
  casier: 'Casier judiciaire',
}

export const TUTEUR_DOCS_LABELS: Record<string, string> = {
  piece_identite: "Pièce d'identité",
  justificatif_domicile: 'Justificatif de domicile',
  acte_naissance: 'Acte de naissance',
  jugement_tutelle: 'Jugement de tutelle',
}

/** Référentiel global pour la page Gestion documentaire (Type K). */
export const ALL_DOCS_LABELS: Record<string, string> = {
  ...ELEVE_DOCS_LABELS,
  ...ENSEIGNANT_DOCS_LABELS,
  ...TUTEUR_DOCS_LABELS,
  autre: 'Autre document',
}

export function countVisibleDocuments(
  documents: readonly { type_document: string }[],
  labels: Record<string, string>,
): number {
  return documents.filter((d) => labels[d.type_document] !== undefined).length
}

// ── Statuts de document (design system §26) ─────────────────────────────────
export const DOCUMENT_STATUS_LABELS: Record<DocumentStatus, string> = {
  brouillon: 'Brouillon',
  en_attente: 'En attente',
  valide: 'Validé',
  archive: 'Archivé',
  erreur: 'Erreur',
}

export const DOCUMENT_STATUS_TONES: Record<DocumentStatus, BadgeTone> = {
  brouillon: 'neutral',
  en_attente: 'warning',
  valide: 'success',
  archive: 'neutral',
  erreur: 'danger',
}

// ── Types de fichier (design system §22) ────────────────────────────────────
export const FILE_TYPE_LABELS: Record<FileType, string> = {
  pdf: 'PDF',
  word: 'Word',
  sheet: 'Excel',
  image: 'Image',
  other: 'Autre',
}

export function fileTypeFromFilename(filename: string): FileType {
  const ext = filename.split('.').pop()?.toLowerCase() ?? ''
  if (ext === 'pdf') return 'pdf'
  if (['doc', 'docx', 'odt'].includes(ext)) return 'word'
  if (['xls', 'xlsx', 'csv'].includes(ext)) return 'sheet'
  if (['jpg', 'jpeg', 'png', 'webp', 'gif', 'bmp', 'heic'].includes(ext)) return 'image'
  return 'other'
}

export function formatFileSize(bytes: number | null | undefined): string {
  if (bytes == null || Number.isNaN(bytes) || bytes < 0) return ''
  if (bytes < 1024) return `${bytes} o`
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} Ko`
  return `${(bytes / (1024 * 1024)).toFixed(1).replace('.', ',')} Mo`
}

// ── Format de fichier (badges de carte, icônes, preview) ────────────────────
function extension(nom: string): string {
  return nom.split('.').pop()?.toLowerCase() ?? ''
}

/** Libellé court du format pour le badge de type (coin haut-droit de la carte). */
export function documentFormatLabel(doc: Pick<DocumentRead, 'nom_fichier_original' | 'nom' | 'type_mime'>): string {
  const nom = doc.nom_fichier_original || doc.nom || ''
  const ext = extension(nom)
  if (ext && ext.length <= 5) return ext.toUpperCase()
  const mime = doc.type_mime ?? ''
  if (mime === 'application/pdf') return 'PDF'
  if (mime.startsWith('image/')) return 'IMG'
  if (mime.includes('word')) return 'DOC'
  return 'FILE'
}

/** Type de fichier générique à partir du MIME / du nom. */
export function typeDocument(doc: Pick<DocumentRead, 'nom_fichier_original' | 'nom' | 'type_mime'>): FileType {
  const mime = doc.type_mime ?? ''
  if (mime === 'application/pdf') return 'pdf'
  if (mime.startsWith('image/')) return 'image'
  if (mime.includes('word') || mime.includes('officedocument')) return 'word'
  if (mime.includes('sheet') || mime.includes('excel') || mime.includes('csv')) return 'sheet'
  const ext = extension(doc.nom_fichier_original || doc.nom || '')
  if (ext === 'pdf') return 'pdf'
  if (['jpg', 'jpeg', 'png', 'webp', 'gif', 'bmp', 'heic'].includes(ext)) return 'image'
  if (['doc', 'docx', 'odt'].includes(ext)) return 'word'
  if (['xls', 'xlsx', 'csv'].includes(ext)) return 'sheet'
  return 'other'
}

export function isDocumentPdf(doc: Pick<DocumentRead, 'type_mime' | 'nom_fichier_original' | 'nom'>): boolean {
  return typeDocument(doc) === 'pdf'
}

export function isDocumentImage(doc: Pick<DocumentRead, 'type_mime' | 'nom_fichier_original' | 'nom'>): boolean {
  return typeDocument(doc) === 'image'
}

/** Construit le modèle UI (§23) à partir d'une réponse backend. */
export function toUiDocument(
  doc: Pick<Document, 'id' | 'filename' | 'taille' | 'mime_type' | 'uploaded_at'> & {
    categorie?: DocumentCategorie
    entite_label?: string
    matricule_eleve?: string | null
    matricule_enseignant?: string | null
    code_tuteur?: string | null
  },
): UiDocument {
  const entityHref =
    doc.matricule_eleve != null
      ? `/app/eleves/${doc.matricule_eleve}`
      : doc.matricule_enseignant != null
        ? `/app/enseignants/${doc.matricule_enseignant}`
        : doc.code_tuteur != null
          ? `/app/tuteurs/${doc.code_tuteur}`
          : undefined

  return {
    id: doc.id,
    name: doc.filename,
    filename: doc.filename,
    type: fileTypeFromFilename(doc.filename),
    // Les documents stockés par l'application sont finalisés/validés (§26).
    status: 'valide',
    sizeBytes: doc.taille ?? undefined,
    mimeType: doc.mime_type ?? undefined,
    createdAt: new Date(doc.uploaded_at),
    entityLabel: doc.entite_label,
    entityType: doc.categorie,
    entityHref,
  }
}