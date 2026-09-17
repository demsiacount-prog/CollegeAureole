import { DocumentCard } from './DocumentCard'
import type { DocumentRead } from './types'

interface DocumentGridProps {
  docs: DocumentRead[]
  onPreview?: (doc: DocumentRead) => void
  onDownload?: (doc: DocumentRead) => void
  onDelete?: (doc: DocumentRead) => void
}

/** Grille de cartes de documents (Type K — gap 10px). */
export function DocumentGrid({ docs, onPreview, onDownload, onDelete }: DocumentGridProps) {
  if (docs.length === 0) return null
  return (
    <div className="flex flex-wrap gap-[10px]">
      {docs.map((doc) => (
        <DocumentCard key={doc.id} doc={doc} onPreview={onPreview} onDownload={onDownload} onDelete={onDelete} />
      ))}
    </div>
  )
}