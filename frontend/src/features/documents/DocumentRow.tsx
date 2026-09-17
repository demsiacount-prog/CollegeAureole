import { Download, Eye, Trash2 } from 'lucide-react'
import { formatDate } from '@/lib/format'
import { Tooltip } from '@/components/ui/Tooltip'
import { documentFormatLabel, formatFileSize, typeDocument } from './labels'
import { FileTypeIcon } from './FileTypeIcon'
import type { DocumentRead } from './types'

interface DocumentRowProps {
  doc: DocumentRead
  onPreview?: (doc: DocumentRead) => void
  onDownload?: (doc: DocumentRead) => void
  onDelete?: (doc: DocumentRead) => void
}

/** Ligne de document (vue liste) — design system Type K. */
export function DocumentRow({ doc, onPreview, onDownload, onDelete }: DocumentRowProps) {
  return (
    <div className="doc-list-row">
      <span className="doc-list-icon">
        <FileTypeIcon type={typeDocument(doc)} size="sm" />
      </span>
      <div className="doc-list-info">
        <Tooltip content={doc.nom}>
          <button type="button" className="doc-list-name block w-full text-left" onClick={() => onPreview?.(doc)}>
            {doc.nom}
          </button>
        </Tooltip>
        <p className="doc-list-meta">
          {documentFormatLabel(doc)} · {formatFileSize(doc.taille_octets ?? doc.taille)} · {formatDate(doc.uploaded_at || doc.created_at)}
        </p>
      </div>
      <div className="doc-list-actions">
        {onPreview && (
          <Tooltip content="Aperçu">
            <button type="button" className="doc-action-btn" onClick={() => onPreview(doc)} aria-label={`Aperçu de ${doc.nom}`}>
              <Eye size={14} strokeWidth={1.75} />
            </button>
          </Tooltip>
        )}
        {onDownload && (
          <Tooltip content="Télécharger">
            <button type="button" className="doc-action-btn" onClick={() => onDownload(doc)} aria-label={`Télécharger ${doc.nom}`}>
              <Download size={14} strokeWidth={1.75} />
            </button>
          </Tooltip>
        )}
        {onDelete && (
          <Tooltip content="Supprimer">
            <button type="button" className="doc-action-btn danger" onClick={() => onDelete(doc)} aria-label={`Supprimer ${doc.nom}`}>
              <Trash2 size={14} strokeWidth={1.75} />
            </button>
          </Tooltip>
        )}
      </div>
    </div>
  )
}