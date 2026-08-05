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

export function noteColor(n: number, bareme: number) {
  const pct = n / bareme
  if (pct >= 0.8) return 'success' as const
  if (pct >= 0.6) return 'neutral' as const
  if (pct >= 0.5) return 'warning' as const
  return 'danger' as const
}

export function appreciation(n: number, bareme: number) {
  const pct = n / bareme
  if (pct >= 0.8) return 'Excellent'
  if (pct >= 0.7) return 'Très bien'
  if (pct >= 0.6) return 'Bien'
  if (pct >= 0.5) return 'Passable'
  return 'Insuffisant'
}
