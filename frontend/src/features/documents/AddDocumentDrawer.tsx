import { type ReactNode, useState } from 'react'
import { FileUp, Loader2 } from 'lucide-react'
import { Drawer } from '@/components/ui/Drawer'
import { Select } from '@/components/ui/Select'
import { Button } from '@/components/ui/Button'
import { clsx } from 'clsx'
import { formatFileSize } from './labels'

interface AddDocumentDrawerProps {
  open: boolean
  onClose: () => void
  title?: string
  labels: Record<string, string>
  /** Section entité (élève/enseignant/tuteur) utilisé par la page Type K. */
  children?: ReactNode
  submitLabel?: string
  onSubmit: (typeDocument: string, file: File) => void | Promise<void>
  submitting?: boolean
}

const ACCEPT = '.pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png,.webp'

/** Drawer d'ajout d'un document (design system §16 zone d'upload / §24). */
export function AddDocumentDrawer({
  open,
  onClose,
  title = 'Ajouter un document',
  labels,
  children,
  submitLabel = 'Importer',
  onSubmit,
  submitting = false,
}: AddDocumentDrawerProps) {
  const entries = Object.entries(labels)
  const [typeDocument, setTypeDocument] = useState(entries[0]?.[0] ?? '')
  const [file, setFile] = useState<File | null>(null)

  const canSubmit = !!file && !submitting

  async function handleSubmit() {
    if (!file) return
    try {
      await onSubmit(typeDocument, file)
      setFile(null)
      onClose()
    } catch {
      // L'erreur est affichée par l'appelant (toast).
    }
  }

  return (
    <Drawer
      open={open}
      onClose={onClose}
      title={title}
      description="Choisissez le type de document puis le fichier à importer."
      footer={
        <>
          <Button variant="secondary" onClick={onClose} disabled={submitting}>
            Annuler
          </Button>
          <Button variant="primary" disabled={!canSubmit} isLoading={submitting} onClick={handleSubmit}>
            <FileUp size={14} strokeWidth={1.75} className="mr-1.5" />
            {submitLabel}
          </Button>
        </>
      }
    >
      <div className="flex flex-col gap-4">
        {children}

        <Select
          label="Type de document"
          value={typeDocument}
          onChange={(e) => setTypeDocument(e.target.value)}
          options={entries.map(([value, label]) => ({ value, label }))}
        />

        <div className="flex flex-col gap-1.5">
          <span className="text-sm font-medium text-[var(--color-ink)]">Fichier</span>
          <label
            className={clsx(
              'flex cursor-pointer flex-col items-center justify-center gap-1.5 rounded-[var(--radius-sm)] border border-dashed px-4 py-6 text-center transition-colors',
              file
                ? 'border-[var(--color-action)] bg-[var(--color-action-wash)]'
                : 'border-[var(--color-border)] bg-[var(--color-surface-2)] hover:border-[var(--color-action)] hover:bg-[var(--color-action-wash)]',
            )}
          >
            {file ? (
              <>
                <p className="max-w-full truncate text-sm font-medium text-[var(--color-ink)]">{file.name}</p>
                <p className="font-mono text-xs text-[var(--color-ink-faint)]">{formatFileSize(file.size)}</p>
              </>
            ) : (
              <>
                <FileUp size={22} strokeWidth={1.75} className="text-[var(--color-ink-faint)]" />
                <p className="text-sm text-[var(--color-ink-dim)]">Sélectionner un fichier</p>
                <p className="text-xs text-[var(--color-ink-faint)]">PDF · DOCX · XLSX · JPG · PNG · max 10 Mo</p>
              </>
            )}
            <input
              type="file"
              accept={ACCEPT}
              className="hidden"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            />
          </label>
        </div>

        {submitting && (
          <p className="flex items-center gap-2 text-sm text-[var(--color-ink-dim)]">
            <Loader2 className="size-4 animate-spin text-[var(--color-action)]" />
            Import en cours…
          </p>
        )}
      </div>
    </Drawer>
  )
}