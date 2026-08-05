import { X } from 'lucide-react'
import { Button } from './Button'

interface Props {
  open: boolean
  onClose: () => void
  onConfirm: () => void
  title: string
  description?: string
  confirmLabel?: string
  variant?: 'danger' | 'success'
  children?: React.ReactNode
}

export function ConfirmDialog({ open, onClose, onConfirm, title, description, confirmLabel = 'Confirmer', variant = 'danger', children }: Props) {
  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="fixed inset-0 bg-black/40" onClick={onClose} />
      <div className="relative z-10 w-full max-w-md rounded-[var(--radius-lg)] border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-xl">
        <div className="flex items-start justify-between mb-4">
          <h3 className="text-lg font-semibold text-[var(--color-ink)]">{title}</h3>
          <button onClick={onClose} className="text-[var(--color-ink-faint)] hover:text-[var(--color-ink)]" aria-label="Fermer">
            <X size={20} strokeWidth={1.75} />
          </button>
        </div>
        {description && <p className="mb-4 text-sm text-[var(--color-ink-dim)]">{description}</p>}
        {children && <div className="mb-4">{children}</div>}
        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={onClose}>
            Annuler
          </Button>
          <Button variant={variant === 'danger' ? 'danger' : 'primary'} onClick={onConfirm}>
            {confirmLabel}
          </Button>
        </div>
      </div>
    </div>
  )
}
