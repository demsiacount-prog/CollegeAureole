import { useEffect } from 'react'
import { AlertTriangle, CheckCircle2, type LucideIcon } from 'lucide-react'
import { clsx } from 'clsx'
import { Button } from './Button'

interface Props {
  open: boolean
  onClose: () => void
  onConfirm: () => void
  title: string
  description?: string
  confirmLabel?: string
  variant?: 'danger' | 'success'
  isLoading?: boolean
  children?: React.ReactNode
}

/** Design system §36 — Modal de confirmation (actions destructives exclusivement). */
export function ConfirmDialog({ open, onClose, onConfirm, title, description, confirmLabel = 'Supprimer', variant = 'danger', isLoading, children }: Props) {
  useEffect(() => {
    if (!open) return
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [open, onClose])

  if (!open) return null

  const Icon: LucideIcon = variant === 'danger' ? AlertTriangle : CheckCircle2

  return (
    <div className="animate-fade-in fixed inset-0 z-[200] flex items-center justify-center bg-black/55">
      <div className="animate-modal-in w-[360px] rounded-[var(--radius-xl)] border border-[var(--border)] bg-[var(--surface)] p-6 shadow-[var(--shadow-float)]">
        <div
          className={clsx(
            'mb-[14px] flex size-9 items-center justify-center rounded-[var(--radius-lg)]',
            variant === 'danger' ? 'bg-[var(--danger-w)] text-[var(--danger)]' : 'bg-[var(--success-w)] text-[var(--success)]',
          )}
        >
          <Icon size={22} strokeWidth={1.75} />
        </div>
        <h3 className="mb-2 font-[var(--font-serif)] text-[16px] font-semibold text-[var(--ink)]">{title}</h3>
        {description && <div className="mb-5 text-[13px] leading-[1.6] text-[var(--ink-dim)]">{description}</div>}
        {children && <div className="mb-5">{children}</div>}
        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={onClose}>
            Annuler
          </Button>
          <Button variant={variant === 'danger' ? 'danger' : 'primary'} onClick={onConfirm} isLoading={isLoading}>
            {confirmLabel}
          </Button>
        </div>
      </div>
    </div>
  )
}