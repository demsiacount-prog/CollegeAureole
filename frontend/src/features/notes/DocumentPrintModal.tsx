import { type ReactNode } from 'react'
import { createPortal } from 'react-dom'
import { Printer, X } from 'lucide-react'
import { Button } from '@/components/ui/Button'

/** Aperçu plein écran d'un document HTML (registre, bulletin annuel…) destiné à
 *  l'impression. La barre d'outils est masquée à l'impression (.no-print) ; seul
 *  le contenu (.print-root) est rendu sur le papier via la feuille print.css. */
export function DocumentPrintModal({
  title,
  onClose,
  children,
  toolbar,
}: {
  title: string
  onClose: () => void
  children: ReactNode
  toolbar?: ReactNode
}) {
  return createPortal(
    <div className="fixed inset-0 z-[60] flex flex-col bg-[var(--surface)]">
      <div className="no-print flex shrink-0 items-center justify-between gap-3 border-b border-[var(--border-soft)] px-4 py-2">
        <span className="truncate text-[13px] font-medium text-[var(--ink)]">{title}</span>
        <div className="flex shrink-0 items-center gap-2">
          {toolbar}
          <Button size="sm" variant="primary" onClick={() => window.print()}>
            <Printer size={13} strokeWidth={1.75} />
            Imprimer
          </Button>
          <Button size="sm" variant="ghost" onClick={onClose}>
            <X size={13} strokeWidth={1.75} />
            Fermer
          </Button>
        </div>
      </div>
      <div className="print-root min-h-0 flex-1 overflow-auto bg-[var(--surface-2)]">
        {children}
      </div>
    </div>,
    document.body,
  )
}