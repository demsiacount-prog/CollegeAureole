export function baremeNiveau(niveau: string): number {
  const n = (niveau ?? '').trim().toLowerCase()
  const ordre = parseInt(niveau, 10)
  if (n.includes('année') || n.includes('annee')) return ordre >= 1 && ordre <= 6 ? 10 : 20
  const estLycee =
    ['terminale', 'tle', 'seconde', 'première', 'premiere', '2nde', '2de'].some((k) => n.includes(k)) ||
    /^1ère/.test(n) ||
    /^1re\b/.test(n)
  if (estLycee) return 20
  if (Number.isNaN(ordre)) return 20
  return ordre >= 1 && ordre <= 6 ? 10 : 20
}

/** Vrai si le niveau est la 6ème année (classe spéciale). */
export function estSixieme(niveau: string): boolean {
  return parseInt(niveau, 10) === 6
}

/** Vrai si le niveau appartient au 1er cycle (1ère-6ème, barème /10). */
export function estEf1(niveau: string): boolean {
  return baremeNiveau(niveau) === 10
}

/** Les coefficients s'appliquent-ils pour cette période d'un niveau donné ?
 *
 * - COMPOSITIONS (1er cycle) : toujours en moyenne simple.
 * - TRIMESTRES EF2/lycée : moyenne pondérée (/20).
 * - TRIMESTRES de la 6ème (classe spéciale) : moyenne pondérée mais sur /10.
 */
export function utiliseCoefficient(niveau: string, type: string): boolean {
  if (type === 'COMPOSITION') return false
  return !estEf1(niveau) || estSixieme(niveau)
}

export function noteColor(n: number, bareme: number) {
  const pct = n / bareme
  if (pct >= 0.8) return 'success' as const
  if (pct >= 0.6) return 'neutral' as const
  if (pct >= 0.5) return 'warning' as const
  return 'danger' as const
}

export function appreciation(n: number, bareme: number) {
  const pct = n / bareme
  if (pct >= 0.9) return 'Excellent'
  if (pct >= 0.8) return 'Très bien'
  if (pct >= 0.7) return 'Bien'
  if (pct >= 0.6) return 'Assez bien'
  if (pct >= 0.5) return 'Passable'
  return 'Insuffisant'
}
