import { clsx } from 'clsx'
import type { ReactNode } from 'react'

interface TooltipProps {
  content?: string
  children: ReactNode
  side?: 'top' | 'bottom'
  className?: string
}

/** Composant Tooltip léger CSS-only : apparaît au group-hover après 300ms. */
export function Tooltip({ content, children, side = 'top', className }: TooltipProps) {
  return (
    <span className={clsx('group/tooltip relative inline-flex', className)}>
      {children}
      {content ? (
        <span
          role="tooltip"
          className={clsx(
            'pointer-events-none absolute z-50 whitespace-nowrap rounded-[var(--radius-sm)] bg-[var(--ink)] px-2 py-1 text-[11px] leading-tight text-white opacity-0 shadow-md transition-opacity duration-150 group-hover/tooltip:opacity-100',
            side === 'top' ? 'bottom-full left-1/2 mb-1.5 -translate-x-1/2' : 'top-full left-1/2 mt-1.5 -translate-x-1/2',
          )}
        >
          {content}
        </span>
      ) : null}
    </span>
  )
}
