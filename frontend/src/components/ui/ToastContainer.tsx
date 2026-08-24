import { CheckCircle, XCircle, Info, X, TriangleAlert } from 'lucide-react'
import { useToasts, type ToastTone } from './toast'
import { useModalStackCount } from './modalStack'

const toneStyles: Record<ToastTone, string> = {
  success: 'border-[var(--color-success)]/20 bg-[var(--color-success)]/10 text-[var(--color-success)]',
  error: 'border-[var(--color-danger)]/20 bg-[var(--color-danger)]/10 text-[var(--color-danger)]',
  info: 'border-[var(--color-info)]/20 bg-[var(--color-info)]/10 text-[var(--color-info)]',
  warning: 'border-[var(--color-warning, #f59e0b)]/30 bg-[var(--color-warning, #f59e0b)]/10 text-[var(--color-warning, #b45309)]',
}

const toneIcons: Record<ToastTone, typeof CheckCircle> = {
  success: CheckCircle,
  error: XCircle,
  info: Info,
  warning: TriangleAlert,
}

export function ToastContainer() {
  const { toasts, dismiss } = useToasts()
  const modalOpen = useModalStackCount() > 0

  if (toasts.length === 0) return null

  return (
    <div
      className={`pointer-events-none fixed top-4 z-[70] flex flex-col gap-2 ${modalOpen ? 'left-4 items-start pr-24' : 'inset-x-0 items-center'}`}
      role="status"
    >
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
