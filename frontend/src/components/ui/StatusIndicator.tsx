import { Loader2, Minus, Check, X } from 'lucide-react'
import { clsx } from 'clsx'

/** Design system §13 — Indicateur d'État.
 *
 *  Liste verticale d'items séquentiels (En attente / En cours / Succès / Erreur /
 *  Ignoré ou Optionnel) utilisée pendant l'installation et les vérifications de
 *  démarrage. Une durée optionnelle (mono) s'affiche pour les items terminés.
 * */
export type IndicatorState = 'pending' | 'running' | 'success' | 'error' | 'skipped'

export interface StatusItem {
  id: string
  label: string
  state: IndicatorState
  /** Durée affichée uniquement pour les items terminés (ex : « 1,2 s »). */
  duration?: string
}

interface StatusIndicatorProps {
  items: StatusItem[]
  className?: string
}

const stateIcon = (state: IndicatorState) => {
  switch (state) {
    case 'running':
      return <Loader2 className="size-3.5 animate-spin text-[var(--color-action)]" strokeWidth={2} />
    case 'success':
      return <Check className="size-3.5 text-[var(--color-success)]" strokeWidth={2.25} />
    case 'error':
      return <X className="size-3.5 text-[var(--color-danger)]" strokeWidth={2.25} />
    case 'skipped':
      return <Minus className="size-3.5 text-[var(--color-ink-faint)]" strokeWidth={2} />
    default: // pending
      return <span className="size-3 rounded-full border border-[var(--color-ink-faint)]" />
  }
}

const labelColor = (state: IndicatorState) => {
  switch (state) {
    case 'running':
      return 'text-[var(--color-ink)]'
    case 'error':
      return 'text-[var(--color-danger)]'
    case 'skipped':
      return 'text-[var(--color-ink-faint)] italic'
    case 'success':
      return 'text-[var(--color-ink-dim)]'
    default:
      return 'text-[var(--color-ink-faint)]'
  }
}

export function StatusIndicator({ items, className }: StatusIndicatorProps) {
  return (
    <ul className={clsx('flex flex-col gap-2.5', className)}>
      {items.map((item) => (
        <li key={item.id} className="flex items-center gap-2.5">
          <span className="flex w-4 shrink-0 justify-center">{stateIcon(item.state)}</span>
          <span className={clsx('min-w-0 flex-1 text-[13px]', labelColor(item.state))}>{item.label}</span>
          {(item.state === 'success' || item.state === 'error') && item.duration && (
            <span className="shrink-0 font-[var(--font-mono)] text-[11px] text-[var(--color-ink-faint)]">
              {item.duration}
            </span>
          )}
        </li>
      ))}
    </ul>
  )
}