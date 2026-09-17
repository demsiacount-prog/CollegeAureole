import { type ReactNode, useEffect, useRef } from 'react'
import { createPortal } from 'react-dom'
import { X } from 'lucide-react'
import { clsx } from 'clsx'

type DrawerSize = 'sm' | 'md' | 'lg'

const WIDTHS: Record<DrawerSize, string> = {
  sm: 'var(--drawer-w-sm)',
  md: 'var(--drawer-w)',
  lg: 'var(--drawer-w-lg)',
}

interface DrawerProps {
  open: boolean
  onClose: () => void
  title: string
  description?: string
  footer?: ReactNode
  size?: DrawerSize
  children: ReactNode
  /** Submit du formulaire (raccourci Ctrl+Entrée / Cmd+Entrée et Ctrl+S). */
  onSubmit?: () => void
}

/** Design system §35 — Drawer (panneau latéral). S'ouvre depuis la droite.
 *  Raccourcis §42 : Ctrl/Cmd+Entrée ou Ctrl/Cmd+S déclenchent `onSubmit`. */
export function Drawer({
  open,
  onClose,
  title,
  description,
  footer,
  size = 'md',
  children,
  onSubmit,
}: DrawerProps) {
  const dialogRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    if (!open) return
    function handleKey(e: KeyboardEvent) {
      if (e.key === 'Escape') {
        onClose()
        return
      }
      if ((e.ctrlKey || e.metaKey) && (e.key === 'Enter' || e.key.toLowerCase() === 's')) {
        e.preventDefault()
        // Priorité au submit explicite du drawer, sinon on soumet le <form> interne
        // (§42 — Ctrl+S / Ctrl+Entrée sauvegardent le formulaire en cours).
        if (onSubmit) {
          onSubmit()
        } else {
          const form = dialogRef.current?.querySelector('form')
          if (form) form.requestSubmit()
        }
      }
    }
    document.addEventListener('keydown', handleKey)
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', handleKey)
      document.body.style.overflow = ''
    }
  }, [open, onClose, onSubmit])

  if (!open) return null

  return createPortal(
    <div className="fixed inset-0 z-[100] flex justify-end">
      <div
        className="animate-fade-in absolute inset-0 bg-black/45"
        onClick={onClose}
        aria-hidden="true"
      />
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="drawer-title"
        className={clsx('animate-drawer-in relative flex h-full flex-col border-l border-[var(--border)] bg-[var(--surface)] shadow-[var(--shadow-float)]')}
        style={{ width: WIDTHS[size], maxWidth: '100vw' }}
      >
        <div className="flex h-[52px] shrink-0 items-center justify-between border-b border-[var(--border)] px-5">
          <h2 id="drawer-title" className="font-[var(--font-serif)] text-[16px] font-semibold text-[var(--ink)]">
            {title}
          </h2>
          <button
            onClick={onClose}
            aria-label="Fermer"
            className="flex size-[30px] items-center justify-center rounded-[var(--radius-md)] text-[var(--ink-faint)] transition-colors duration-80 hover:bg-[var(--surface-2)] hover:text-[var(--ink)]"
          >
            <X className="size-[15px]" strokeWidth={1.75} />
          </button>
        </div>
        {description && (
          <p className="shrink-0 px-5 pb-3 text-[12.5px] -mt-1 text-[var(--ink-faint)]">{description}</p>
        )}
        <div className="flex-1 overflow-y-auto px-5 py-5">{children}</div>
        {footer && (
          <div className="flex shrink-0 items-center justify-end gap-2 border-t border-[var(--border)] bg-[var(--surface)] px-5 py-3">
            {footer}
          </div>
        )}
      </div>
    </div>,
    document.body,
  )
}