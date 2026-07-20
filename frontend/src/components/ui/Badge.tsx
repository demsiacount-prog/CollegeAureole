import type { HTMLAttributes } from 'react'
import { clsx } from 'clsx'

type Tone = 'neutral' | 'success' | 'warning' | 'danger' | 'info' | 'halo'

const toneClasses: Record<Tone, string> = {
  neutral: 'bg-[var(--color-surface-3)] text-[var(--color-ink-dim)]',
  success: 'bg-[var(--color-success-wash)] text-[var(--color-success)]',
  warning: 'bg-[var(--color-warning-wash)] text-[var(--color-warning)]',
  danger: 'bg-[var(--color-danger-wash)] text-[var(--color-danger)]',
  info: 'bg-[var(--color-info-wash)] text-[var(--color-info)]',
  halo: 'bg-[var(--color-halo-wash)] text-[var(--color-halo-bright)]',
}

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  tone?: Tone
}

export function Badge({ tone = 'neutral', className, ...rest }: BadgeProps) {
  return (
    <span
      className={clsx(
        'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
        toneClasses[tone],
        className,
      )}
      {...rest}
    />
  )
}

const ROLE_LABELS: Record<string, string> = {
  admin: 'Administrateur',
  directeur: 'Directeur',
  comptable: 'Comptable',
}

export function RoleBadge({ role }: { role: string }) {
  const tone: Tone = role === 'admin' ? 'halo' : role === 'directeur' ? 'info' : 'success'
  return <Badge tone={tone}>{ROLE_LABELS[role] ?? role}</Badge>
}
