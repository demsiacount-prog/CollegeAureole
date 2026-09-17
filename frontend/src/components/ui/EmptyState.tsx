import type { ReactNode } from 'react'
import type { LucideIcon } from 'lucide-react'

export function EmptyState({
  title,
  message,
  action,
  icon: Icon,
}: {
  title?: string
  message: string
  action?: ReactNode
  icon?: LucideIcon
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-2.5 px-6 py-12 text-center text-[var(--ink-faint)]">
      {Icon && <Icon className="mb-1 size-10" strokeWidth={1.25} />}
      {title && <p className="text-[14px] font-medium text-[var(--ink-dim)]">{title}</p>}
      <p className="max-w-[280px] text-[12.5px] leading-[1.5] text-[var(--ink-faint)]">{message}</p>
      {action && <div className="mt-1">{action}</div>}
    </div>
  )
}