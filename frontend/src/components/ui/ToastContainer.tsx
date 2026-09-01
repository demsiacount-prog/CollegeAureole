import { CheckCircle, XCircle, Info, X, TriangleAlert } from 'lucide-react'
import { useToasts, type ToastTone } from './toast'

const leftBorder: Record<ToastTone, string> = {
  success: '#a3c05f',
  error: '#e0707f',
  info: '#5b9dc4',
  warning: '#c98a4a',
}
const toneIcons: Record<ToastTone, typeof CheckCircle> = {
  success: CheckCircle,
  error: XCircle,
  info: Info,
  warning: TriangleAlert,
}
const toneIconColor: Record<ToastTone, string> = {
  success: 'text-[var(--color-success)]',
  error: 'text-[var(--color-danger)]',
  info: 'text-[var(--color-info)]',
  warning: 'text-[var(--color-warning)]',
}
const progressColor: Record<ToastTone, string> = {
  success: 'var(--color-success)',
  error: 'var(--color-danger)',
  info: 'var(--color-info)',
  warning: 'var(--color-warning)',
}

/** Design system §14 — Toast & Notifications.
 *  Coin inférieur droit, max 3 visibles, bordure gauche 3px, barre d'auto-dismiss. */
export function ToastContainer() {
  const { toasts, dismiss } = useToasts()
  if (toasts.length === 0) return null

  // Empilement vers le haut, maximum 3 visibles (le 4e remplace le 1er via l'auto-dismiss).
  const visible = toasts.slice(-3)

  return (
    <div
      className="pointer-events-none fixed bottom-6 right-6 z-[70] flex w-[360px] max-w-[calc(100vw-3rem)] flex-col-reverse justify-start gap-3"
      role="status"
      aria-live="polite"
    >
      {visible.map((t) => {
        const Icon = toneIcons[t.tone]
        return (
          <div
            key={t.id}
            className="animate-toast-in pointer-events-auto relative flex items-start gap-3 overflow-hidden rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-4 shadow-[0_4px_16px_rgba(0,0,0,0.4)]"
            style={{ borderLeft: `3px solid ${leftBorder[t.tone]}` }}
          >
            <Icon strokeWidth={1.75} className={`size-[18px] shrink-0 ${toneIconColor[t.tone]}`} />
            <span className="flex-1 pt-0.5 text-sm font-semibold text-[var(--color-ink)]">{t.message}</span>
            {t.action && (
              <button
                onClick={() => {
                  t.action?.onClick()
                  dismiss(t.id)
                }}
                className="shrink-0 rounded-[var(--radius-sm)] border border-[var(--color-border)] px-2 py-0.5 text-xs font-semibold text-[var(--color-ink-dim)] transition-opacity hover:opacity-80"
              >
                {t.action.label}
              </button>
            )}
            <button
              onClick={() => dismiss(t.id)}
              className="shrink-0 rounded p-0.5 text-[var(--color-ink-faint)] opacity-60 transition-opacity hover:opacity-100"
              aria-label="Fermer la notification"
            >
              <X strokeWidth={1.75} className="size-4" />
            </button>
            {t.duration > 0 && (
              <span className="absolute bottom-0 left-0 h-[2px] w-full bg-[var(--color-surface-3)]">
                <span
                  className="toast-progress block h-full w-full"
                  style={{
                    backgroundColor: progressColor[t.tone],
                    animationDuration: `${Math.max(t.duration, 100)}ms`,
                  }}
                />
              </span>
            )}
          </div>
        )
      })}
    </div>
  )
}
