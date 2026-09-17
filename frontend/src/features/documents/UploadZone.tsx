import { type DragEvent, useRef, useState } from 'react'
import { clsx } from 'clsx'
import { UploadCloud } from 'lucide-react'

interface UploadZoneProps {
  onSelect: (file: File) => void
  disabled?: boolean
  compact?: boolean
}

/** Zone de dépôt glisser-déposer (Type K) — clic ou drag & drop. */
export function UploadZone({ onSelect, disabled, compact }: UploadZoneProps) {
  const inputRef = useRef<HTMLInputElement | null>(null)
  const [dragOver, setDragOver] = useState(false)

  function handleDrop(e: DragEvent) {
    e.preventDefault()
    setDragOver(false)
    if (disabled) return
    const file = e.dataTransfer.files?.[0]
    if (file) onSelect(file)
  }

  return (
    <div
      role="button"
      tabIndex={0}
      aria-label="Ajouter un fichier"
      className={clsx('upload-zone', dragOver && 'drag-over', compact && 'upload-zone-compact')}
      onClick={() => !disabled && inputRef.current?.click()}
      onKeyDown={(e) => {
        if ((e.key === 'Enter' || e.key === ' ') && !disabled) inputRef.current?.click()
      }}
      onDragOver={(e) => {
        e.preventDefault()
        if (!disabled) setDragOver(true)
      }}
      onDragLeave={() => setDragOver(false)}
      onDrop={handleDrop}
      aria-disabled={disabled}
    >
      <span className="upload-zone-icon">
        <UploadCloud size={compact ? 22 : 28} strokeWidth={1.5} />
      </span>
      <p className="upload-zone-title">Glisser-déposer un fichier ou cliquer pour parcourir</p>
      <p className="upload-zone-sub">PDF, JPG, PNG, DOCX · max 10 Mo</p>
      <input
        ref={inputRef}
        type="file"
        className="hidden"
        accept=".pdf,.jpg,.jpeg,.png,.webp,.doc,.docx"
        onChange={(e) => {
          const file = e.target.files?.[0]
          if (file) onSelect(file)
          e.target.value = ''
        }}
      />
    </div>
  )
}