import { clsx } from 'clsx'
import type { FileType, FileTypeSize } from './types'
import { fileTypeFromFilename } from './labels'

// Initiales affichées dans l'icône (design system §22 — Inter 700, uppercase).
const INITIALS: Record<FileType, string> = {
  pdf: 'PDF',
  word: 'DOC',
  sheet: 'XLS',
  image: 'IMG',
  other: 'FILE',
}

const ARIA_LABEL: Record<FileType, string> = {
  pdf: 'Document PDF',
  word: 'Document Word',
  sheet: 'Document Excel',
  image: 'Document image',
  other: 'Document autre',
}

interface FileTypeIconProps {
  /** Type explicite du fichier. Si absent, déduit de l'extension du nom. */
  type?: FileType
  /** Taille de l'icône — ratio 5:6 (portrait A4). */
  size?: FileTypeSize
  filename?: string
  className?: string
}

/** Icône de type de fichier (§22) — rectangle arrondi coloré aux initiales du
 *  format, coin supérieur droit rogné (dog-ear). */
export function FileTypeIcon({ type, size = 'md', filename, className }: FileTypeIconProps) {
  const resolved: FileType = type ?? (filename ? fileTypeFromFilename(filename) : 'other')
  return (
    <span
      role="img"
      aria-label={ARIA_LABEL[resolved]}
      className={clsx('doc-icon shrink-0', `doc-icon-${size}`, `doc-icon-${resolved}`, className)}
    >
      {INITIALS[resolved]}
    </span>
  )
}