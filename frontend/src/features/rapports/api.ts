import { api } from '@/lib/api'
import type {
  ClassementResponse,
  FicheNotesCompoResponse,
  FicheRenseignementsResponse,
  FicheRenseignementsPremierCycleResponse,
  FicheSuivi,
  PropositionPassage,
  RapportsParams,
  RapportMoyennes,
  RapportRentree,
} from './types'

export type {
  ClassementResponse,
  ClassementClasse,
  ClassementEleve,
  FicheNotesCompoMatiere,
  FicheNotesCompoResponse,
  FicheRenseignementsCellule,
  FicheRenseignementsLigne,
  FicheRenseignementsPersonnel,
  FicheRenseignementsResponse,
  FicheRensPCLigne,
  FicheRensPCPersonnel,
  FicheRenseignementsPremierCycleResponse,
  FicheSuivi,
  FicheSuiviLigne,
  FicheSuiviPassage,
  MoyenneTrimestre,
  NoteParMatiere,
  ParcoursAnnee,
  PropositionPassage,
  RapportsParams,
  RapportMoyennes,
  EleveMoyenne,
  ClasseMoyennes,
  EleveProposition,
  ClasseProposition,
  RapportRentree,
  RapportRentreeClasse,
  RapportRentreeCycle,
} from './types'

function rapportParams(params?: RapportsParams): Record<string, number> {
  const out: Record<string, number> = {}
  if (params?.anneeId) out.annee_id = params.anneeId
  if (params?.classeId) out.classe_id = params.classeId
  return out
}

/** Récupère les octets d'un PDF généré (avec l'authentification axios).
 *  Réutilisé par l'aperçu PDF (PdfViewerModal) et par les téléchargements. */
export async function recupererPdf(
  url: string,
  params?: Record<string, string | number | undefined>,
): Promise<ArrayBuffer> {
  const res = await api.get(url, { params, responseType: 'arraybuffer' })
  return res.data as ArrayBuffer
}

export async function fetchMoyennesAnnuelles(params?: RapportsParams): Promise<RapportMoyennes> {
  const res = await api.get<RapportMoyennes>('/api/rapports/moyennes-annuelles', {
    params: rapportParams(params),
  })
  return res.data
}

export async function fetchPropositionPassage(params?: RapportsParams): Promise<PropositionPassage> {
  const res = await api.get<PropositionPassage>('/api/rapports/proposition-passage', {
    params: rapportParams(params),
  })
  return res.data
}

export async function fetchFicheSuivi(matricule: string, params?: RapportsParams): Promise<FicheSuivi> {
  const res = await api.get<FicheSuivi>(`/api/rapports/eleves/${matricule}/fiche-suivi`, {
    params: rapportParams(params),
  })
  return res.data
}

export async function fetchRapportRentree(params?: RapportsParams): Promise<RapportRentree> {
  const res = await api.get<RapportRentree>('/api/rapports/rentree', {
    params: rapportParams(params),
  })
  return res.data
}

function declencherTelechargement(data: Blob, disposition?: string, fallback = 'document.pdf') {
  const match = disposition?.match(/filename="?([^"]+)"?/)
  const nom = match?.[1] ?? fallback
  const url = window.URL.createObjectURL(data)
  const a = document.createElement('a')
  a.href = url
  a.download = nom
  document.body.appendChild(a)
  a.click()
  a.remove()
  window.URL.revokeObjectURL(url)
}

// ─── Classement des élèves (doc1) ──────────────────────────────────────────────

export async function fetchClassement(params?: RapportsParams): Promise<ClassementResponse> {
  const res = await api.get<ClassementResponse>('/api/rapports/classement', {
    params: rapportParams(params),
  })
  return res.data
}

// ─── Fiche de renseignements de rentrée, 2nd cycle (doc6) ─────────────────────

export async function fetchFicheRenseignements(params?: RapportsParams): Promise<FicheRenseignementsResponse> {
  const res = await api.get<FicheRenseignementsResponse>('/api/rapports/fiche-renseignements', {
    params: rapportParams(params),
  })
  return res.data
}

// ─── Fiche de renseignements de rentrée, 1er cycle (doc5) ─────────────────────

export async function fetchFicheRenseignementsPremierCycle(
  params?: RapportsParams,
): Promise<FicheRenseignementsPremierCycleResponse> {
  const res = await api.get<FicheRenseignementsPremierCycleResponse>(
    '/api/rapports/fiche-renseignements-premier-cycle',
    { params: rapportParams(params) },
  )
  return res.data
}

// ─── Fiche de notes mensuelle / de composition, élève (doc7 + doc3) ──────────

export interface NotesCompoParams extends RapportsParams {
  trimestreId?: number
}

export async function fetchFicheNotesCompositions(
  matricule: string,
  params?: NotesCompoParams,
): Promise<FicheNotesCompoResponse> {
  const res = await api.get<FicheNotesCompoResponse>(`/api/rapports/eleves/${matricule}/fiche-notes-compositions`, {
    params: rapportParams(params),
  })
  return res.data
}

export async function downloadFicheNotesCompositionsPdf(
  matricule: string,
  params?: NotesCompoParams,
): Promise<void> {
  declencherTelechargement(
    new Blob([await recupererPdf(`/api/rapports/eleves/${matricule}/fiche-notes-compositions/pdf`, rapportParams(params))], {
      type: 'application/pdf',
    }),
    undefined,
    'Fiche_de_notes_compositions.pdf',
  )
}

export async function fetchFicheNotesCompositionsPdf(
  matricule: string,
  params?: NotesCompoParams,
): Promise<ArrayBuffer> {
  return recupererPdf(`/api/rapports/eleves/${matricule}/fiche-notes-compositions/pdf`, rapportParams(params))
}

// (doc8 — carnet scolaire supprimé : l'affichage se fait par les bulletins)