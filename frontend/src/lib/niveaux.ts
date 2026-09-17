export const NIVEAUX_JARDIN = [
  'Petite Section',
  'Moyenne Section',
  'Grande Section',
]

export const NIVEAUX_FONDAMENTAL = [
  '1ère Année', '2ème Année', '3ème Année',
  '4ème Année', '5ème Année', '6ème Année',
  '7ème Année', '8ème Année', '9ème Année',
]

export const NIVEAUX_CLASSES = [...NIVEAUX_JARDIN, ...NIVEAUX_FONDAMENTAL]

export function estNiveauJardin(niveau: string | null | undefined): boolean {
  return NIVEAUX_JARDIN.includes((niveau ?? '').trim())
}

/** Ordre du niveau (1 → 1ère Année … 9 → 9ème Année) ; null pour le jardin. */
export function niveauOrdre(niveau: string | null | undefined): number | null {
  const n = parseInt(niveau ?? '', 10)
  return Number.isNaN(n) ? null : n
}