import type { ReactNode } from 'react'

export function EmptyState({
  title,
  message,
  action,
}: {
  title?: string
  message: string
  action?: ReactNode
}) {
  return (
    <div className="flex flex-col items-center rounded-[var(--radius-md)] border border-dashed border-[var(--color-border)] px-4 py-10 text-center">
      {title && <p className="mb-1 font-medium text-[var(--color-ink)]">{title}</p>}
      <p className="text-sm text-[var(--color-ink-faint)]">{message}</p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  )
}
