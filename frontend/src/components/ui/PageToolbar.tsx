import { Search } from 'lucide-react'
import type { ReactNode } from 'react'

/** Design system §32 — PageToolbar : recherche, filtres, vues + CTA contextuels. */
export function PageToolbar({ children }: { children: ReactNode }) {
  return (
    <div className="flex flex-wrap items-center gap-[7px] whitespace-nowrap border-b border-[var(--border)] px-[18px] py-2.5">
      {children}
    </div>
  )
}

/** Champ de recherche de la toolbar (§32 .toolbar-search) — 30px de haut, surface, 200px. */
export function ToolbarSearch({ className, ...rest }: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <div className="flex h-[30px] w-[200px] shrink-0 items-center gap-1.5 rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] px-2.5 transition-colors focus-within:border-[var(--action)]">
      <Search className="size-3.5 shrink-0 text-[var(--ink-faint)]" strokeWidth={1.75} />
      <input
        className={['w-full bg-transparent text-[12.5px] text-[var(--ink)] outline-none placeholder:text-[var(--ink-faint)]', className].filter(Boolean).join(' ')}
        {...rest}
      />
    </div>
  )
}

/** Filtre (Select) de la toolbar (§32 .toolbar-filter) — 30px, fond surface. */
export function ToolbarFilter({ className, children, ...rest }: React.SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <label className="flex h-[30px] shrink-0 cursor-pointer items-center gap-1 rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] pl-2.5 pr-1.5 text-[12.5px] text-[var(--ink-dim)]">
      <select
        className={['cursor-pointer appearance-none bg-transparent text-[12.5px] text-[var(--ink-dim)] outline-none', className].filter(Boolean).join(' ')}
        {...rest}
      >
        {children}
      </select>
      <span className="pointer-events-none text-[10px] text-[var(--ink-faint)]">▾</span>
    </label>
  )
}

/** Filtre date de la toolbar — 30px, fond surface. `prefix` affiche un libellé court ("Du"/"Au"). */
export function ToolbarDate({ prefix, className, ...rest }: { prefix?: string } & React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <label className="flex h-[30px] shrink-0 cursor-pointer items-center gap-1.5 rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] px-2 text-[11px] text-[var(--ink-faint)]">
      {prefix && <span>{prefix}</span>}
      <input
        type="date"
        className={['cursor-pointer bg-transparent text-[12px] text-[var(--ink)] outline-none', className].filter(Boolean).join(' ')}
        {...rest}
      />
    </label>
  )
}

/** Espaceur flexible de la toolbar. */
export function ToolbarSpacer() {
  return <div className="flex-1" />
}

/** Zone droite de la toolbar (CTA intra-section, sous-total…). */
export function ToolbarEnd({ children }: { children: ReactNode }) {
  return <div className="ml-auto flex items-center gap-2">{children}</div>
}