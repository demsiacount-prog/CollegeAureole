import { DocumentRow } from './DocumentRow'
import type { DocumentRead } from './types'

interface DocumentListProps {
  docs: DocumentRead[]
  onPreview?: (doc: DocumentRead) => void
  onDownload?: (doc: DocumentRead) => void
  onDelete?: (doc: DocumentRead) => void
}

/** Liste ligne par ligne (Type K). */
export function DocumentList({ docs, onPreview, onDownload, onDelete }: DocumentListProps) {
  if (docs.length === 0) return null
  return (
    <div className="doc-list">
      {docs.map((doc) => (
        <DocumentRow key={doc.id} doc={doc} onPreview={onPreview} onDownload={onDownload} onDelete={onDelete} />
      ))}
    </div>
  )
}