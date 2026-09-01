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
}

export function Breadcrumbs({ items, className }: { items: BreadcrumbItem[]; className?: string }) {
  return (
    <nav aria-label="Fil d'Ariane" className={className}>
      <ol className="flex items-center gap-1 text-xs text-[var(--color-ink-faint)]">
        {items.map((item, i) => {
          const last = i === items.length - 1
          return (
            <li key={i} className="flex items-center gap-1">
              {i > 0 && <ChevronRight className="size-3" strokeWidth={1.75} />}
              {item.to && !last ? (
                <Link to={item.to} className="transition-colors hover:text-[var(--color-ink-dim)]">{item.label}</Link>
              ) : (
                <span className={last ? 'text-[var(--color-ink-dim)]' : ''} aria-current={last ? 'page' : undefined}>
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

export function PageHeader({ title, count, countLabel, actionLabel, onAction, subtitle, breadcrumb, eyebrow, moduleColor }: PageHeaderProps) {
  const module = useCurrentModule()
  const color = moduleColor ?? module?.moduleColor ?? null
  const label = eyebrow ?? (module?.title === 'Vue d’ensemble' ? undefined : module?.title)
  return (
    <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-end">
      <div>
        {breadcrumb && breadcrumb.length > 0 && (
          <Breadcrumbs items={breadcrumb} className="mb-1.5" />
        )}
        {label && color && (
          <p
            className="mb-1 text-xs font-semibold uppercase tracking-[0.14em]"
            style={{ color }}
          >
            {label}
          </p>
        )}
        <h1 className="font-[var(--font-display)] text-[28px] font-semibold leading-tight tracking-tight text-[var(--color-ink)]">
          {title}
        </h1>
        {subtitle ?? (count !== undefined && countLabel && (
          <p className="mt-1 text-sm text-[var(--color-ink-dim)]">
            {count} {countLabel}
          </p>
        ))}
      </div>
      {actionLabel && onAction && (
        <Button variant="primary" onClick={onAction}>
          <Plus strokeWidth={1.75} className="size-4 mr-1.5" />
          {actionLabel}
        </Button>
      )}
    </div>
  )
}
