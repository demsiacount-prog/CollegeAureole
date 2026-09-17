import { useState } from 'react'
import { toast } from '@/components/ui/toast'
import { extractErrorMessage } from '@/lib/api'
import { PdfViewerModal } from './PdfViewerModal'

interface UsePdfApercuProps {
  titre: string
  chargeur: () => Promise<ArrayBuffer>
  onTelecharger?: () => void
  initialScroll?: 'vertical' | 'horizontal'
}

/** Aperçu « vrai PDF » (lecteur pdf.js) pour les rapports générés.
 *  « Aperçu » ouvre le lecteur ; « Imprimer » l'ouvre puis lance l'impression. */
export function usePdfApercu({ titre, chargeur, onTelecharger, initialScroll = 'vertical' }: UsePdfApercuProps) {
  const [apercu, setApercu] = useState<{ data: ArrayBuffer; autoImprim: boolean } | null>(null)
  const [chargement, setChargement] = useState(false)

  const joindre = async (autoImprim: boolean) => {
    if (chargement) return
    setChargement(true)
    try {
      const data = await chargeur()
      setApercu({ data, autoImprim })
    } catch (err) {
      toast(extractErrorMessage(err, 'Impossible de charger le document.'), 'error')
    } finally {
      setChargement(false)
    }
  }

  const element =
    apercu && (
      <PdfViewerModal
        data={apercu.data}
        filename={titre}
        initialScroll={initialScroll}
        impressionAuto={apercu.autoImprim}
        onImpressionAutoFini={() => setApercu((a) => (a ? { ...a, autoImprim: false } : a))}
        onClose={() => setApercu(null)}
        onDownload={onTelecharger}
      />
    )

  return {
    chargement,
    element,
    ouvrirApercu: () => joindre(false),
    ouvrirImprimer: () => joindre(true),
  }
}