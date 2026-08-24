import { useEffect, useState } from 'react'
import { createPortal } from 'react-dom'
import { X, Download, FileText, FileQuestion } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Spinner } from '@/components/ui/Spinner'
import { fetchDocumentBlob } from './api'
import type { Document } from './types'

function extension(filename: string): string {
  return filename.split('.').pop()?.toLowerCase() ?? ''
}

function useObjectUrl(doc: Document | null) {
  const [url, setUrl] = useState<string | null>(null)
  const [blobType, setBlobType] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!doc) {
      setUrl(null)
      setBlobType('')
      setError('')
      return
    }
    let cancelled = false
    let createdUrl: string | null = null
    setLoading(true)
    setError('')
    fetchDocumentBlob(doc.id)
      .then((blob) => {
        if (cancelled) return
        setBlobType(blob.type)
        createdUrl = URL.createObjectURL(blob)
        setUrl(createdUrl)
      })
      .catch(() => {
        if (!cancelled) setError('Impossible de charger le document.')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
      if (createdUrl) URL.revokeObjectURL(createdUrl)
    }
  }, [doc])

  return { url, blobType, error, loading }
}

function kind(doc: Document, blobType: string): 'image' | 'pdf' | 'other' {
  const ext = extension(doc.filename)
  if (ext === 'pdf' || blobType === 'application/pdf' || blobType === 'application/x-pdf') return 'pdf'
  if (['jpg', 'jpeg', 'png', 'webp', 'gif', 'bmp'].includes(ext) || blobType.startsWith('image/')) return 'image'
  return 'other'
}

function PdfViewer({ url }: { url: string }) {
  return (
    <iframe
      src={url}
      className="mx-auto block h-[calc(100vh-140px)] w-full max-w-4xl rounded-[var(--radius-sm)] border border-[var(--color-border)] bg-white"
      title="Aperçu PDF"
    />
  )
}

export function DocumentPreview({ doc, onClose }: { doc: Document | null; onClose: () => void }) {
  const { url, blobType, error, loading } = useObjectUrl(doc)
  const docKind = doc ? kind(doc, blobType) : 'other'
  const image = docKind === 'image'
  const pdf = docKind === 'pdf'

  useEffect(() => {
    if (!doc) return
    function handleKey(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handleKey)
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', handleKey)
      document.body.style.overflow = ''
    }
  }, [doc, onClose])

  if (!doc) return null

  return createPortal(
    <div className="fixed inset-0 z-50 flex flex-col bg-black/70 backdrop-blur-[2px]">
      <div className="flex items-center justify-between gap-3 border-b border-[var(--color-border)] bg-[var(--color-surface)] px-5 py-3">
        <div className="flex min-w-0 items-center gap-2">
          <FileText size={16} className="shrink-0 text-[var(--color-ink-dim)]" />
          <p className="truncate text-sm font-medium text-[var(--color-ink)]">{doc.filename}</p>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          {url && (
            <a href={url} download={doc.filename}>
              <Button type="button" variant="secondary" size="sm">
                <Download size={14} strokeWidth={1.75} /> Télécharger
              </Button>
            </a>
          )}
          <button
            onClick={onClose}
            aria-label="Fermer"
            className="rounded-[var(--radius-sm)] p-1.5 text-[var(--color-ink-faint)] transition-colors hover:bg-[var(--color-surface-2)] hover:text-[var(--color-ink)]"
          >
            <X className="size-5" />
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-auto p-6">
        {loading && (
          <div className="flex justify-center py-16">
            <Spinner label="Chargement du document…" />
          </div>
        )}
        {error && <p className="text-center text-sm text-[var(--color-danger)]">{error}</p>}
        {url && image && (
          <img
            src={url}
            alt={doc.filename}
            className="mx-auto block max-h-[calc(100vh-140px)] max-w-full rounded-[var(--radius-sm)] border border-[var(--color-border)] bg-white shadow-[var(--shadow-soft)]"
          />
        )}
        {url && pdf && <PdfViewer url={url} />}
        {url && !image && !pdf && (
          <div className="mx-auto flex max-w-sm flex-col items-center gap-3 rounded-[var(--radius-sm)] border border-[var(--color-border)] bg-[var(--color-surface)] p-8 text-center">
            <FileQuestion size={32} className="text-[var(--color-ink-faint)]" strokeWidth={1.75} />
            <p className="text-sm text-[var(--color-ink-dim)]">
              Ce format ne peut pas être affiché dans l'application.
            </p>
            <a href={url} download={doc.filename}>
              <Button type="button" variant="primary" size="sm">
                <Download size={14} strokeWidth={1.75} /> Télécharger le fichier
              </Button>
            </a>
          </div>
        )}
      </div>
    </div>,
    document.body,
  )
}
