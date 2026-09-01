import { useState } from 'react'
import { ImageOff } from 'lucide-react'
import { clsx } from 'clsx'
import { urlAbsolue } from '@/lib/server'

interface LogoEtablissementProps {
  src?: string | null
  nom?: string
  className?: string
  label?: boolean
}

export function LogoEtablissement({ src, nom, className, label = false }: LogoEtablissementProps) {
  const [enErreur, setEnErreur] = useState(false)
  if (src && !enErreur) {
    return (
      <img
        src={urlAbsolue(src)}
        alt={nom ? `Logo de ${nom}` : 'Logo de l’établissement'}
        className={clsx('object-contain', className)}
        loading="lazy"
        decoding="async"
        onError={() => setEnErreur(true)}
      />
    )
  }
  return (
    <span
      className={clsx(
        'flex items-center justify-center overflow-hidden rounded-lg border border-dashed border-[var(--color-border)] bg-[var(--color-surface-2)] text-[var(--color-ink-faint)]',
        label && 'flex-col gap-1',
        className,
      )}
      role="img"
      aria-label="Logo de l’établissement non fourni"
      title="Logo manquant"
    >
      <ImageOff className={clsx('shrink-0', label ? 'size-4' : 'size-1/2')} />
      {label && (
        <span className="max-w-full px-1 text-center text-[10px] font-semibold uppercase leading-tight tracking-wide">
          Logo manquant
        </span>
      )}
    </span>
  )
}
