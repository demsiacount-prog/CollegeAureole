import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { ChevronRight, Plus } from 'lucide-react'
import { Button } from './Button'
import { useCurrentModule } from '@/routes/useModule'

export interface BreadcrumbItem {
  label: string
  to?: string
}

interface PageHeaderProps {
  title: string
  count?: number
  countLabel?: string
  actionLabel?: string
  onAction?: () => void
  subtitle?: ReactNode
  breadcrumb?: BreadcrumbItem[]
  eyebrow?: string
  moduleColor?: string
  /** Résumé de section : chips de stats passées via <StatChip />. */
  summary?: ReactNode
}

export function StatChip({ value, label }: { value: string | number; label: string }) {
  return (
    <span className="hidden h-[34px] items-center gap-1.5 whitespace-nowrap rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] px-2.5 lg:flex">
      <span className="text-[13px] font-semibold tabular-nums text-[var(--ink)]">{value}</span>
      <span className="text-[10px] leading-tight text-[var(--ink-faint)]">{label}</span>
    </span>
  )
}

export function Breadcrumbs({ items, className }: { items: BreadcrumbItem[]; className?: string }) {
  return (
    <nav aria-label="Fil d'Ariane" className={className}>
      <ol className="flex items-center gap-1 text-xs text-[var(--ink-faint)]">
        {items.map((item, i) => {
          const last = i === items.length - 1
          return (
            <li key={i} className="flex items-center gap-1">
              {i > 0 && <ChevronRight className="size-3" strokeWidth={1.75} />}
              {item.to && !last ? (
                <Link to={item.to} className="transition-colors hover:text-[var(--ink-dim)]">{item.label}</Link>
              ) : (
                <span className={last ? 'text-[var(--ink-dim)]' : ''} aria-current={last ? 'page' : undefined}>
                  {item.label}
                </span>
              )}
            </li>
          )
        })}
      </ol>
    </nav>
  )
}

/** Design system §32 — En-tête de page (Type A v2) : titre 18px serif + count-badge,
 *  sous-titre, résumé (chips) et CTA principal. Largeur 66px, padding-x = gouttière. */
export function PageHeader({ title, count, countLabel, actionLabel, onAction, subtitle, breadcrumb, eyebrow, moduleColor, summary }: PageHeaderProps) {
  const module = useCurrentModule()
  const color = moduleColor ?? module?.moduleColor ?? null
  const subtitleNode = subtitle ?? (count !== undefined && countLabel ? countLabel : undefined)
  return (
    <section className="flex min-h-[62px] w-full items-center gap-4 px-[18px]" aria-label={title}>
      <div className="min-w-0 flex-1">
        {breadcrumb && breadcrumb.length > 0 && (
          <Breadcrumbs items={breadcrumb} className="mb-1" />
        )}
        {eyebrow && color && (
          <p className="mb-0.5 text-[10px] font-semibold uppercase tracking-[0.14em]" style={{ color }}>
            {eyebrow}
          </p>
        )}
        <div className="flex items-center gap-2.5">
          <h1 className="truncate font-[var(--font-serif)] text-[18px] font-semibold leading-[1.2] tracking-[-0.01em] text-[var(--ink)]">
            {title}
          </h1>
          {count !== undefined && (
            <span className="inline-flex shrink-0 items-center rounded-[var(--radius-sm)] bg-[var(--surface-3)] px-1.5 py-px text-[11px] font-medium leading-tight tabular-nums text-[var(--ink-dim)]">
              {count}
            </span>
          )}
        </div>
        {subtitleNode && (
          <p className="mt-0.5 truncate text-[12.5px] text-[var(--ink-faint)]">{subtitleNode}</p>
        )}
      </div>
      {summary && (
        <div className="flex shrink-0 items-center gap-1.5">{summary}</div>
      )}
      {actionLabel && onAction && (
        <Button variant="primary" size="lg" onClick={onAction}>
          <Plus strokeWidth={1.75} className="mr-1.5 size-4" />
          {actionLabel}
        </Button>
      )}
    </section>
  )
}