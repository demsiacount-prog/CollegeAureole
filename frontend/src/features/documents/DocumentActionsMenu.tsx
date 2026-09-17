import { useEffect, useRef, useState } from 'react'
import { MoreVertical, Eye, Download, Printer, Pencil, Trash2 } from 'lucide-react'
import { clsx } from 'clsx'

interface DocumentActionsMenuProps {
  onView?: () => void
  onDownload?: () => void
  onPrint?: () => void
  onDelete?: () => void
  /** false → « Renommer » grisé (documents validés/archivés : §27). */
  canRename?: boolean
}

/** Menu d'actions document `⋯` (design system §24/§27) : popover 180px. */
export function DocumentActionsMenu({
  onView,
  onDownload,
  onPrint,
  onDelete,
  canRename = false,
}: DocumentActionsMenuProps) {
  const [open, setOpen] = useState(false)
  const rootRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open) return
    function onDocClick(e: MouseEvent) {
      if (rootRef.current && !rootRef.current.contains(e.target as Node)) setOpen(false)
    }
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') setOpen(false)
    }
    document.addEventListener('mousedown', onDocClick)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('mousedown', onDocClick)
      document.removeEventListener('keydown', onKey)
    }
  }, [open])

  const item = (icon: React.ReactNode, label: string, onClick?: () => void, disabled = false, danger = false) => (
    <button
      type="button"
      disabled={disabled}
      onClick={() => {
        if (disabled) return
        setOpen(false)
        onClick?.()
      }}
      className={clsx(
        'flex w-full items-center gap-2.5 px-3 py-2 text-left text-sm transition-colors',
        disabled
          ? 'cursor-not-allowed text-[var(--color-ink-disabled)]'
          : danger
            ? 'text-[var(--color-danger)] hover:bg-[var(--color-danger-wash)]'
            : 'text-[var(--color-ink-dim)] hover:bg-[var(--color-surface-3)] hover:text-[var(--color-ink)]',
      )}
    >
      {icon}
      {label}
    </button>
  )

  return (
    <div ref={rootRef} className="relative">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-label="Actions du document"
        aria-haspopup="menu"
        aria-expanded={open}
        className="inline-flex size-8 items-center justify-center rounded-[var(--radius-sm)] text-[var(--color-ink-faint)] transition-colors hover:bg-[var(--color-surface-3)] hover:text-[var(--color-ink)]"
      >
        <MoreVertical size={16} strokeWidth={1.75} />
      </button>
      {open && (
        <div
          role="menu"
          className="absolute right-0 top-9 z-[var(--z-dropdown)] w-[180px] overflow-hidden rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface)] py-1 shadow-[var(--shadow-float)]"
        >
          {onView && item(<Eye size={15} strokeWidth={1.75} />, 'Ouvrir dans la visionneuse', onView)}
          {onDownload && item(<Download size={15} strokeWidth={1.75} />, 'Télécharger', onDownload)}
          {onPrint && item(<Printer size={15} strokeWidth={1.75} />, 'Imprimer', onPrint)}
          {item(<Pencil size={15} strokeWidth={1.75} />, 'Renommer', undefined, !canRename)}
          <div className="my-1 h-px bg-[var(--color-border-soft)]" />
          {onDelete && item(<Trash2 size={15} strokeWidth={1.75} />, 'Supprimer', onDelete, false, true)}
        </div>
      )}
    </div>
  )
}