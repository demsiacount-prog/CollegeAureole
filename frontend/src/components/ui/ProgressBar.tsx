import { clsx } from 'clsx'

/** Design system §12 — Barre de Progression.
 *
 *  Variante A (« installer », 8px) : progression déterminée, remplissage `--action`.
 *  Variante B (« splash », 2px) : planche fixe en bas, remplissage `--halo`,
 *    phase indéterminée (shimmer) avant 15 % puis déterminée ensuite.
 *  Variante C (« wizard », 3px) : progression par étapes, `--action`.
 * */
type Variant = 'installer' | 'splash' | 'wizard'

interface ProgressBarProps {
  /** Progression 0–100. Laisse non défini pour afficher l'animation indéterminée. */
  value?: number
  variant?: Variant
  indeterminate?: boolean
  className?: string
}

const sizes: Record<Variant, string> = {
  installer: 'h-2 rounded-full',
  splash: 'h-[3px] rounded-none',
  wizard: 'h-[3px] rounded-full',
}

const trackColors: Record<Variant, string> = {
  installer: 'bg-[var(--color-surface-3)]',
  splash: 'bg-[var(--color-surface-2)]',
  wizard: 'bg-[var(--color-surface-3)]',
}

const fillColors: Record<Variant, string> = {
  installer: 'bg-[var(--color-action)]',
  splash: 'bg-[var(--color-halo)]',
  wizard: 'bg-[var(--color-action)]',
}

const transitions: Record<Variant, string> = {
  installer: 'transition-[width] duration-300 ease-out',
  splash: 'transition-[width] duration-300 ease-out',
  wizard: 'transition-[width] duration-[400ms] ease-in-out',
}

export function ProgressBar({ value, variant = 'installer', indeterminate = false, className }: ProgressBarProps) {
  const isIndeterminate = indeterminate || (variant === 'splash' && (value == null || value < 15))

  return (
    <div
      role="progressbar"
      aria-valuenow={value != null ? Math.round(value) : undefined}
      aria-valuemin={0}
      aria-valuemax={100}
      className={clsx('w-full overflow-hidden', sizes[variant], trackColors[variant], className)}
    >
      {isIndeterminate ? (
        <span className={clsx('block h-full w-full animate-[shimmer-sweep_1.2s_ease-in-out_infinite]', fillColors[variant])} />
      ) : (
        <span
          className={clsx('block h-full', transitions[variant], fillColors[variant])}
          style={{ width: `${Math.min(Math.max(value ?? 0, 0), 100)}%` }}
        />
      )}
    </div>
  )
}