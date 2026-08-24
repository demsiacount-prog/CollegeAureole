import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { FileText, Trash2, Upload } from 'lucide-react'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { toast } from '@/components/ui/toast'
import { extractErrorMessage } from '@/lib/api'
import { scheduleDeleteWithUndo } from '@/lib/undoDelete'
import { deleteDocument } from './api'
import { DocumentPreview } from './DocumentPreview'
import type { Document } from './types'

interface Props {
  documents: Document[]
  labels: Record<string, string>
  invalidateKey: string[]
  upload: (typeDocument: string, file: File) => Promise<Document>
  canEdit?: boolean
}

export function DocumentsTab({ documents, labels, invalidateKey, upload, canEdit = true }: Props) {
  const qc = useQueryClient()
  const [deleting, setDeleting] = useState<Document | null>(null)
  const [preview, setPreview] = useState<Document | null>(null)

  const uploadMut = useMutation({
    mutationFn: ({ typeDocument, file }: { typeDocument: string; file: File }) => upload(typeDocument, file),
    onSuccess: () => {
      toast('Document importé')
      qc.invalidateQueries({ queryKey: invalidateKey })
    },
    onError: (e) => toast(extractErrorMessage(e), 'error'),
  })

  const deleteMut = useMutation({
    mutationFn: deleteDocument,
    onSuccess: () => {
      toast('Document supprimé')
      qc.invalidateQueries({ queryKey: invalidateKey })
      setDeleting(null)
    },
    onError: (e) => toast(extractErrorMessage(e), 'error'),
  })

  const grouped: Record<string, Document[]> = {}
  for (const doc of documents) {
    ;(grouped[doc.type_document] ??= []).push(doc)
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-3">
        {Object.entries(labels).map(([type, label]) => {
          const existing = grouped[type]
          return (
            <Card key={type} className="flex-1 min-w-[200px] p-4">
              <p className="mb-2 text-sm font-medium text-[var(--color-ink)]">{label}</p>
              {existing && existing.length > 0 ? (
                <div className="space-y-2">
                  {existing.map((doc) => (
                    <div key={doc.id} className="flex items-center justify-between rounded border border-[var(--color-border-soft)] px-3 py-2">
                      <button
                        onClick={() => setPreview(doc)}
                        title="Afficher dans l'application"
                        className="flex min-w-0 items-center gap-2 text-xs text-[var(--color-brand-blue)] hover:underline"
                      >
                        <FileText size={14} strokeWidth={1.75} className="shrink-0" />
                        <span className="truncate">{doc.filename}</span>
                      </button>
                      {canEdit && (
                        <Button
                          variant="icon"
                          tone="danger"
                          size="icon"
                          onClick={() => setDeleting(doc)}
                          aria-label="Supprimer ce document"
                        >
                          <Trash2 size={14} strokeWidth={1.75} />
                        </Button>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-[var(--color-ink-faint)]">Aucun fichier</p>
              )}
              {canEdit && (
                <label className="mt-2 flex cursor-pointer items-center justify-center gap-2 rounded border border-dashed border-[var(--color-border)] px-3 py-2 text-xs text-[var(--color-ink-dim)] hover:bg-[var(--color-surface-2)]">
                  <Upload size={14} strokeWidth={1.75} />
                  Importer
                  <input
                    type="file"
                    accept=".pdf,.jpg,.jpeg,.png"
                    className="hidden"
                    onChange={(e) => {
                      const file = e.target.files?.[0]
                      if (file) uploadMut.mutate({ typeDocument: type, file })
                    }}
                  />
                </label>
              )}
            </Card>
          )
        })}
      </div>

      <ConfirmDialog
        open={!!deleting}
        onClose={() => setDeleting(null)}
        onConfirm={() => {
          if (deleting) {
            setDeleting(null)
            scheduleDeleteWithUndo(() => deleteMut.mutate(deleting.id), 'Document supprimé.')
          }
        }}
        title="Supprimer ce document ?"
        description={`Supprimer ${deleting?.filename} ?`}
        confirmLabel="Supprimer"
        variant="danger"
      />

      <DocumentPreview doc={preview} onClose={() => setPreview(null)} />
    </div>
  )
}
