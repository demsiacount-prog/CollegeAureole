import { CheckCircle, XCircle, Info, X } from 'lucide-react'
import { useToasts, type ToastTone } from './toast'

const toneStyles: Record<ToastTone, string> = {
  success: 'border-[var(--color-success)]/20 bg-[var(--color-success)]/10 text-[var(--color-success)]',
  error: 'border-[var(--color-danger)]/20 bg-[var(--color-danger)]/10 text-[var(--color-danger)]',
  info: 'border-[var(--color-info)]/20 bg-[var(--color-info)]/10 text-[var(--color-info)]',
}

const toneIcons: Record<ToastTone, typeof CheckCircle> = {
  success: CheckCircle,
  error: XCircle,
  info: Info,
}

export function ToastContainer() {
  const { toasts, dismiss } = useToasts()

  if (toasts.length === 0) return null

  return (
    <div className="pointer-events-none fixed right-4 top-4 z-50 flex flex-col items-end gap-2" role="status">
      {toasts.map((t) => {
        const Icon = toneIcons[t.tone]
        return (
          <div
            key={t.id}
            className={`pointer-events-auto flex items-center gap-3 rounded-[var(--radius-sm)] border px-4 py-2.5 text-sm font-medium shadow-[var(--shadow-soft)] ${toneStyles[t.tone]}`}
          >
            <Icon strokeWidth={1.75} className="size-4 shrink-0" />
            <span>{t.message}</span>
            {t.action && (
              <button
                onClick={() => {
                  t.action?.onClick()
                  dismiss(t.id)
                }}
                className="ml-1 shrink-0 rounded-[var(--radius-sm)] border border-current px-2 py-0.5 text-xs font-semibold transition-opacity hover:opacity-80"
              >
                {t.action.label}
              </button>
            )}
            <button
              onClick={() => dismiss(t.id)}
              className="ml-2 shrink-0 rounded p-0.5 opacity-60 transition-opacity hover:opacity-100"
            >
              <X strokeWidth={1.75} className="size-3.5" />
            </button>
          </div>
        )
      })}
    </div>
  )
}
