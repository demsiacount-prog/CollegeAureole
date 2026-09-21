import type { HTMLAttributes } from 'react'
import { clsx } from 'clsx'

type Tone = 'neutral' | 'success' | 'warning' | 'danger' | 'info'

export type BadgeTone = Tone

const toneClasses: Record<Tone, string> = {
  neutral: 'bg-[var(--surface-3)] text-[var(--ink-dim)]',
  success: 'bg-[var(--success-w)] text-[var(--success)]',
  warning: 'bg-[var(--warning-w)] text-[var(--warning)]',
  danger: 'bg-[var(--danger-w)] text-[var(--danger)]',
  info: 'bg-[var(--info-w)] text-[var(--info)]',
}

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  tone?: Tone
}

export function Badge({ tone = 'neutral', className, ...rest }: BadgeProps) {
  return (
    <span
      className={clsx(
        'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs ',
        toneClasses[tone],
        className,
      )}
      {...rest}
    />
  )
}
