import { useEffect, useState } from 'react'
import { clsx } from 'clsx'
import { Download, Eye, Trash2 } from 'lucide-react'
import { formatDate } from '@/lib/format'
import { Tooltip } from '@/components/ui/Tooltip'
import { fetchDocumentBlob } from './api'
import { documentFormatLabel, formatFileSize, isDocumentImage } from './labels'
import { FileTypeIcon } from './FileTypeIcon'
import { typeDocument } from './labels'
import type { DocumentRead } from './types'

/** Miniature réelle pour les documents image (chargée via l'API authentifiée).
 *  Les PDF et autres formats restent sur l'icône de type de fichier. */
function DocumentPreview({ doc }: { doc: DocumentRead }) {
  const [url, setUrl] = useState<string | null>(null)
  const image = isDocumentImage(doc)

  useEffect(() => {
    if (!image) return
    let objectUrl: string | null = null
    let cancelled = false
    fetchDocumentBlob(doc.id)
      .then((blob) => {
        if (cancelled) return
        objectUrl = URL.createObjectURL(blob)
        setUrl(objectUrl)
      })
      .catch(() => {
        /* pas de miniature : on garde l'icône */
      })
    return () => {
      cancelled = true
      if (objectUrl) URL.revokeObjectURL(objectUrl)
    }
  }, [doc.id, image])

  if (image && url) {
    return <img src={url} alt={doc.nom} className="size-full object-cover" />
  }
  return (
    <span className="doc-type-icon flex items-center justify-center">
      <FileTypeIcon type={typeDocument(doc)} size="lg" />
    </span>
  )
}

interface DocumentCardProps {
  doc: DocumentRead
  onPreview?: (doc: DocumentRead) => void
  onDownload?: (doc: DocumentRead) => void
  onDelete?: (doc: DocumentRead) => void
}

/** Carte de document (vue grille) — design system Type K. */
export function DocumentCard({ doc, onPreview, onDownload, onDelete }: DocumentCardProps) {
  return (
    <div className="doc-card w-[160px] shrink-0">
      <button type="button" className="doc-card-preview block w-full" onClick={() => onPreview?.(doc)} aria-label={`Aperçu de ${doc.nom}`}>
        <DocumentPreview doc={doc} />
        <span className={clsx('doc-type-badge', typeDocument(doc))}>{documentFormatLabel(doc)}</span>
      </button>
      <div className="doc-card-body">
        <Tooltip content={doc.nom}>
          <button type="button" onClick={() => onPreview?.(doc)} className="doc-card-name block w-full text-left">
            {doc.nom}
          </button>
        </Tooltip>
        <div className="doc-card-meta">
          <span>{formatFileSize(doc.taille_octets ?? doc.taille)}</span>
          <span>{formatDate(doc.uploaded_at || doc.created_at)}</span>
        </div>
      </div>
      <div className="doc-card-actions">
        {onPreview && (
          <Tooltip content="Aperçu">
            <button type="button" className="doc-action-btn" onClick={() => onPreview(doc)} aria-label={`Aperçu de ${doc.nom}`}>
              <Eye size={13} strokeWidth={1.75} />
            </button>
          </Tooltip>
        )}
        {onDownload && (
          <Tooltip content="Télécharger">
            <button type="button" className="doc-action-btn" onClick={() => onDownload(doc)} aria-label={`Télécharger ${doc.nom}`}>
              <Download size={13} strokeWidth={1.75} />
            </button>
          </Tooltip>
        )}
        {onDelete && (
          <Tooltip content="Supprimer">
            <button type="button" className="doc-action-btn danger" onClick={() => onDelete(doc)} aria-label={`Supprimer ${doc.nom}`}>
              <Trash2 size={13} strokeWidth={1.75} />
            </button>
          </Tooltip>
        )}
        <span className="flex-1" />
      </div>
    </div>
  )
}