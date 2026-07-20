import { clsx } from 'clsx'

function initials(nom: string, prenom: string) {
  return `${prenom.charAt(0)}${nom.charAt(0)}`.toUpperCase()
}

export function Avatar({
  nom,
  prenom,
  haloed = false,
  size = 'md',
}: {
  nom: string
  prenom: string
  haloed?: boolean
  size?: 'sm' | 'md' | 'lg'
}) {
  const sizeClasses = {
    sm: 'size-7 text-[11px]',
    md: 'size-9 text-sm',
    lg: 'size-14 text-lg',
  }[size]

  return (
    <div
      className={clsx(
        'flex shrink-0 items-center justify-center rounded-full font-[var(--font-display)] font-medium',
        'bg-[var(--color-surface-3)] text-[var(--color-halo-bright)] border border-[var(--color-border)]',
        haloed && 'halo-ring',
        sizeClasses,
      )}
    >
      {initials(nom, prenom)}
    </div>
  )
}
