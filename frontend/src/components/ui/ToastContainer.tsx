import { CheckCircle, XCircle, Info, X, TriangleAlert } from 'lucide-react'
import { useToasts, type ToastTone } from './toast'

const toneInfo: Record<ToastTone, { icon: typeof CheckCircle; color: string; bg: string }> = {
  success: { icon: CheckCircle, color: 'var(--success)', bg: 'rgba(163,192,95,0.10)' },
  error: { icon: XCircle, color: 'var(--danger)', bg: 'rgba(224,112,127,0.10)' },
  info: { icon: Info, color: 'var(--action)', bg: 'rgba(45,110,232,0.10)' },
  warning: { icon: TriangleAlert, color: 'var(--warning)', bg: 'rgba(201,138,74,0.10)' },
}

const progressColor: Record<ToastTone, string> = {
  success: 'var(--success)',
  error: 'var(--danger)',
  info: 'var(--action)',
  warning: 'var(--warning)',
}

/** Design system §37 — Toasts & Notifications.
 *  Coin inférieur droit, stack vertical, disparition automatique (4000 ms),
 *  barre de progression, fermeture manuelle. */
export function ToastContainer() {
  const { toasts, dismiss } = useToasts()
  if (toasts.length === 0) return null

  // Le plus récent en bas de la pile (empilement vertical, chevauchement limité).
  const visible = toasts.slice(-3)

  const hasDanger = visible.some((t) => t.tone === 'error')

  return (
    <div
      className="pointer-events-none fixed bottom-5 right-5 z-[300] flex w-[360px] max-w-[calc(100vw-2.5rem)] flex-col-reverse justify-start gap-2"
      role="status"
      aria-live={hasDanger ? 'assertive' : 'polite'}
    >
      {visible.map((t) => {
        const info = toneInfo[t.tone]
        const Icon = info.icon
        return (
          <div
            key={t.id}
            className="animate-toast-in pointer-events-auto relative flex items-start gap-2.5 overflow-hidden rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--surface-2)] px-3.5 py-3 shadow-[var(--shadow-float)]"
            style={{ minWidth: 280, maxWidth: 380 }}
          >
            <span
              className="mt-px inline-flex size-[18px] shrink-0 items-center justify-center rounded-[var(--radius-sm)]"
              style={{ backgroundColor: info.bg, color: info.color }}
            >
              <Icon className="size-4" strokeWidth={1.75} />
            </span>
            <span className="flex-1 pt-[1px]">
              {t.title && <span className="block text-[13px] font-medium leading-tight text-[var(--ink)]">{t.title}</span>}
              <span
                className={t.title ? 'mt-0.5 block text-[12px] leading-tight text-[var(--ink-dim)]' : 'block text-[13px] font-medium leading-tight text-[var(--ink)]'}
              >
                {t.message}
              </span>
              {t.action && (
                <button
                  onClick={() => {
                    t.action?.onClick()
                    dismiss(t.id)
                  }}
                  className="mt-1 shrink-0 rounded-[var(--radius-sm)] border border-[var(--border)] px-2 py-0.5 text-xs font-semibold text-[var(--ink-dim)] transition-opacity hover:opacity-80"
                >
                  {t.action.label}
                </button>
              )}
            </span>
            <button
              onClick={() => dismiss(t.id)}
              className="shrink-0 rounded p-0.5 text-[var(--ink-faint)] opacity-60 transition-opacity hover:opacity-100"
              aria-label="Fermer la notification"
            >
              <X strokeWidth={1.75} className="size-3.5" />
            </button>
            {t.duration > 0 && (
              <span
                className="toast-progress absolute bottom-0 left-0 block h-[2px] w-full"
                style={{ backgroundColor: progressColor[t.tone], animationDuration: `${Math.max(t.duration, 100)}ms` }}
              />
            )}
          </div>
        )
      })}
    </div>
  )
}