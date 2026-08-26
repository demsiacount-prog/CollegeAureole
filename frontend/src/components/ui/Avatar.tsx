import { useState } from 'react'
import { clsx } from 'clsx'
import { urlAbsolue } from '@/lib/server'

function initials(nom: string, prenom: string) {
  return `${prenom.charAt(0)}${nom.charAt(0)}`.toUpperCase()
}

export function Avatar({
  nom,
  prenom,
  photo,
  highlighted = false,
  size = 'md',
}: {
  nom: string
  prenom: string
  photo?: string | null
  highlighted?: boolean
  size?: 'sm' | 'md' | 'lg'
}) {
  const [failed, setFailed] = useState(false)
  const sizeClasses = {
    sm: 'size-7 text-[11px]',
    md: 'size-9 text-sm',
    lg: 'size-14 text-lg',
  }[size]

  if (photo && !failed) {
    return (
      <img
        src={urlAbsolue(photo)}
        alt={`${prenom} ${nom}`}
        loading="lazy"
        decoding="async"
        onError={() => setFailed(true)}
        className={clsx(
          'shrink-0 rounded-full border border-[var(--color-border)] object-cover',
          highlighted && 'shadow-[0_0_0_2px_var(--color-base),0_0_0_4px_var(--color-brand)]',
          sizeClasses,
        )}
      />
    )
  }

  return (
    <div
      className={clsx(
        'flex shrink-0 items-center justify-center rounded-full font-medium',
        'bg-[var(--color-surface-3)] text-[var(--color-ink)] border border-[var(--color-border)]',
        highlighted && 'shadow-[0_0_0_2px_var(--color-base),0_0_0_4px_var(--color-brand)]',
        sizeClasses,
      )}
    >
      {initials(nom, prenom)}
    </div>
  )
}
