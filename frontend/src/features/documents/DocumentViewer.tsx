import { useEffect, useState } from 'react'
import { createPortal } from 'react-dom'
import { ArrowLeft, Download, FileWarning, Printer, ZoomIn, ZoomOut } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Tooltip } from '@/components/ui/Tooltip'
import { Spinner } from '@/components/ui/Spinner'
import { downloadBlob, fetchDocumentBlob } from './api'
import { isDocumentImage, typeDocument } from './labels'
import { FileTypeIcon } from './FileTypeIcon'
import type { DocumentRead } from './types'

const ZOOM_LEVELS = [0.6, 0.75, 0.9, 1.0, 1.15, 1.3, 1.5, 1.75, 2.0]
const ZOOM_DEFAULT = 1.0

function zoomIn(current: number): number {
  return ZOOM_LEVELS[ZOOM_LEVELS.indexOf(current) + 1] ?? current
}
function zoomOut(current: number): number {
  return ZOOM_LEVELS[ZOOM_LEVELS.indexOf(current) - 1] ?? current
}

interface DocumentViewerProps {
  doc: DocumentRead | null
  onClose: () => void
  onOpenUpload?: () => void
}

/** Visionneuse de document plein écran (Type L v6.0) — overlay qui recouvre
 *  l'intégralité de l'application (sidebar + topbar comprises).
 *  Seules les images bénéficient d'un aperçu ; les autres formats (PDF, …)
 *  sont proposés au téléchargement. */
export function DocumentViewer({ doc, onClose, onOpenUpload }: DocumentViewerProps) {
  const [blobUrl, setBlobUrl] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [zoom, setZoom] = useState(ZOOM_DEFAULT)

  useEffect(() => {
    if (!doc) return
    let cancelled = false
    let objectUrl: string | null = null

    setBlobUrl(null)
    setZoom(ZOOM_DEFAULT)
    setError('')
    setLoading(true)

    const isImage = isDocumentImage(doc)

    fetchDocumentBlob(doc.id)
      .then(async (blob) => {
        if (cancelled) return
        if (isImage) {
          objectUrl = URL.createObjectURL(blob)
          if (!cancelled) setBlobUrl(objectUrl)
        } else {
          // PDF ou autre format : pas d'aperçu intégré, téléchargement seul.
          setError('Aperçu non disponible pour ce format.')
        }
      })
      .catch(() => {
        if (!cancelled) setError('Impossible de charger le document.')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
      if (objectUrl) URL.revokeObjectURL(objectUrl)
    }
  }, [doc])

  useEffect(() => {
    if (!doc) return
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') {
        onClose()
        return
      }
      const cible = e.target as HTMLElement
      const saisie = cible instanceof HTMLInputElement || cible instanceof HTMLTextAreaElement || cible.isContentEditable
      if (saisie) return
      if (e.key === '+' || e.key === '=') setZoom((z) => zoomIn(z))
      else if (e.key === '-') setZoom((z) => zoomOut(z))
      else if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's') {
        e.preventDefault()
        void handleDownload()
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [doc, onClose])

  if (!doc) return null

  async function handleDownload() {
    if (!doc) return
    downloadBlob(await fetchDocumentBlob(doc.id), doc.nom)
  }

  const isImage = isDocumentImage(doc) && !!blobUrl

  return (
    createPortal(
      <div className="doc-viewer" role="dialog" aria-modal="true" aria-label="Visionneuse de document">
        <div className="doc-viewer-header">
          <Tooltip content="Retour (Esc)">
            <button type="button" className="doc-viewer-back" onClick={onClose}>
              <ArrowLeft size={14} strokeWidth={1.75} />
              Retour
            </button>
          </Tooltip>
          <span className="doc-viewer-divider" aria-hidden="true" />
          <div className="doc-viewer-title">
            <FileTypeIcon type={typeDocument(doc)} size="xs" />
            <Tooltip content={doc.nom}>
              <span className="truncate">{doc.nom}</span>
            </Tooltip>
          </div>
          <div className="doc-viewer-actions">
            {onOpenUpload && (
              <Tooltip content="Ajouter un document">
                <button type="button" className="btn-icon" onClick={onOpenUpload} aria-label="Ajouter un document">
                  <span className="text-[15px] leading-none">＋</span>
                </button>
              </Tooltip>
            )}
            <Tooltip content="Télécharger (Ctrl+S)">
              <button type="button" className="btn-icon" onClick={() => void handleDownload()} aria-label="Télécharger">
                <Download size={14} strokeWidth={1.75} />
              </button>
            </Tooltip>
            {isImage && (
              <Tooltip content="Imprimer (Ctrl+P)">
                <button type="button" className="btn-icon" onClick={() => window.print()} aria-label="Imprimer">
                  <Printer size={14} strokeWidth={1.75} />
                </button>
              </Tooltip>
            )}
          </div>
        </div>

        <div className="doc-viewer-body">
          {loading && (
            <div className="flex items-center justify-center py-20">
              <Spinner label="Chargement du document…" />
            </div>
          )}
          {!loading && error && (
            <div className="flex flex-col items-center justify-center gap-3 px-6 py-16 text-center">
              <FileWarning size={34} strokeWidth={1.5} className="text-[var(--ink-faint)]" />
              <p className="max-w-[260px] text-[12.5px] leading-[1.5] text-[var(--ink-dim)]">{error}</p>
              <Button variant="primary" size="sm" onClick={() => void handleDownload()}>
                <Download size={13} strokeWidth={1.75} className="mr-1.5" />
                Télécharger le fichier
              </Button>
            </div>
          )}
          {!loading && !error && blobUrl && (
            <div className="vpaper">
              <img
                src={blobUrl}
                alt={doc.nom}
                className="doc-viewer-image"
                style={{ transform: `scale(${zoom})` }}
              />
            </div>
          )}
        </div>

        {isImage && (
          <div className="doc-viewer-status">
            <span className="doc-viewer-pages" />
            <div className="doc-viewer-zoom">
              <Tooltip content="Zoom arrière">
                <button type="button" className="doc-action-btn" onClick={() => setZoom((z) => zoomOut(z))} disabled={zoom <= ZOOM_LEVELS[0]}>
                  <ZoomOut size={13} strokeWidth={1.75} />
                </button>
              </Tooltip>
              <span className="zoom-level">{Math.round(zoom * 100)}%</span>
              <Tooltip content="Zoom avant">
                <button type="button" className="doc-action-btn" onClick={() => setZoom((z) => zoomIn(z))} disabled={zoom >= ZOOM_LEVELS[ZOOM_LEVELS.length - 1]}>
                  <ZoomIn size={13} strokeWidth={1.75} />
                </button>
              </Tooltip>
            </div>
          </div>
        )}
      </div>,
      document.body,
    )
  )
}