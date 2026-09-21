import type { ReactNode } from 'react'
import { Download, Eye, FileText, Printer } from 'lucide-react'
import { Button } from '@/components/ui/Button'

/** Ligne de document au look partagé (pièces jointes du dossier, carnet,
 *  fiche de suivi, fiche mensuelle…) : nom + Aperçu / Imprimer / Télécharger,
 *  avec emplacement pour une action supplémentaire (suppression par ex.). */
export function DocumentActionRow({
  label,
  onApercu,
  onImprimer,
  onTelecharger,
  actions,
}: {
  label: string
  onApercu: () => void
  onImprimer: () => void
  onTelecharger: () => void
  actions?: ReactNode
}) {
  return (
    <div className="flex items-center justify-between gap-3 rounded border border-[var(--border-soft)] px-3 py-2">
      <div className="flex min-w-0 items-center gap-2">
        <FileText size={14} strokeWidth={1.75} className="shrink-0 text-[var(--ink-faint)]" />
        <span className="truncate text-xs text-[var(--ink)]">{label}</span>
      </div>
      <div className="flex shrink-0 items-center gap-1.5">
        <Button size="sm" variant="secondary" onClick={onApercu}>
          <Eye size={13} strokeWidth={1.75} />
          Aperçu
        </Button>
        <Button size="sm" variant="secondary" onClick={onImprimer}>
          <Printer size={13} strokeWidth={1.75} />
          Imprimer
        </Button>
        <Button size="sm" variant="secondary" onClick={onTelecharger}>
          <Download size={13} strokeWidth={1.75} />
          Télécharger
        </Button>
        {actions}
      </div>
    </div>
  )
}