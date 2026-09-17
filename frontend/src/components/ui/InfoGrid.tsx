import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'

/** Type C v2 — Section d'informations (§ grille d'informations).
 *  Titre de section 10px uppercase + grille 3 colonnes de champs. */
export function InfoSection({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="mb-[18px]">
      <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.08em] text-[var(--ink-faint)]">
        {title}
      </p>
      <div className="grid grid-cols-1 gap-2 md:grid-cols-2 xl:grid-cols-3">{children}</div>
    </div>
  )
}

interface InfoFieldProps {
  label: string
  value?: ReactNode
  /** Lien vers une autre entité (couleur action + curseur pointer). */
  to?: string
  /** Valeur code / matricule / téléphone (police mono). */
  mono?: boolean
}

/** Type C v2 — Champ de la grille d'informations (.info-field). */
export function InfoField({ label, value, to, mono }: InfoFieldProps) {
  const isEmpty = value == null || value === '' || value === '—'
  const inner = isEmpty ? (
    <span className="text-[13px] font-medium text-[var(--ink-disabled)]">—</span>
  ) : (
    <span className={mono ? 'font-[var(--font-mono)] text-[12px]' : ''}>{value}</span>
  )

  return (
    <div className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] px-[11px] py-[9px]">
      <p className="mb-0.5 text-[10.5px] text-[var(--ink-faint)]">{label}</p>
      <div className="text-[13px] font-medium text-[var(--ink)]">
        {to ? (
          <Link to={to} className="text-[var(--action)] no-underline transition-colors hover:text-[var(--action-dk)]">
            {inner}
          </Link>
        ) : (
          inner
        )}
      </div>
    </div>
  )
}