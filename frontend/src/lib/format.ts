export function formatDate(value: string | null | undefined): string {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric' })
}

export function formatMontant(value: number | null | undefined): string {
  if (value === null || value === undefined) return '—'
  return new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'XOF', maximumFractionDigits: 0 }).format(value)
}

// Le barème est obligatoire : EF1 est noté /10, EF2/lycée sur /20 — aucun
// défaut implicite pour ne jamais afficher un mauvais dénominateur.
export function formatMoyenne(value: number | null | undefined, bareme: number): string {
  if (value === null || value === undefined) return '—'
  return `${value.toFixed(2)} / ${bareme}`
}
