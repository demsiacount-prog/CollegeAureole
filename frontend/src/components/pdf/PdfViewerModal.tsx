import { useEffect, useRef, useState } from 'react'
import {
  ChevronLeft,
  ChevronRight,
  Columns2,
  Download,
  FileWarning,
  LayoutPanelLeft,
  Maximize2,
  Minimize2,
  Printer,
  Rows3,
  Search,
  SpellCheck2,
  X,
  ZoomIn,
  ZoomOut,
} from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Spinner } from '@/components/ui/Spinner'
import { Tooltip } from '@/components/ui/Tooltip'
import pdfWorkerUrl from 'pdfjs-dist/build/pdf.worker.min.mjs?url'
import 'pdfjs-dist/web/pdf_viewer.css'
import './pdfViewer.css'

type PdfModule = typeof import('pdfjs-dist/web/pdf_viewer.mjs')
type PdfViewerType = InstanceType<PdfModule['PDFViewer']>
type SimpleLinkServiceType = InstanceType<PdfModule['SimpleLinkService']>
type EventBusType = InstanceType<PdfModule['EventBus']>
type ScrollModeEnum = PdfModule['ScrollMode']
type SpreadModeEnum = PdfModule['SpreadMode']

interface PdfViewerModalProps {
  data: ArrayBuffer
  filename?: string
  initialScroll?: 'vertical' | 'horizontal'
  impressionAuto?: boolean
  onImpressionAutoFini?: () => void
  onClose: () => void
  onDownload?: () => void
  downloading?: boolean
}

const PRESETS = [0.5, 0.67, 0.75, 0.9, 1, 1.1, 1.25, 1.5, 2, 2.5, 3, 4]

let modulePromise: Promise<PdfModule> | null = null
function chargerModule(): Promise<PdfModule> {
  modulePromise ??= import('pdfjs-dist/web/pdf_viewer.mjs') as Promise<PdfModule>
  return modulePromise
}

function getPrintHost(): HTMLDivElement {
  let el = document.getElementById('pdfv-print-host') as HTMLDivElement | null
  if (!el) {
    el = document.createElement('div')
    el.id = 'pdfv-print-host'
    document.body.appendChild(el)
  }
  return el
}

export function PdfViewerModal({
  data,
  filename = 'Document',
  initialScroll = 'vertical',
  impressionAuto = false,
  onImpressionAutoFini,
  onClose,
  onDownload,
  downloading,
}: PdfViewerModalProps) {
  const rootRef = useRef<HTMLDivElement | null>(null)
  const scrollerRef = useRef<HTMLDivElement | null>(null)
  const viewerRef = useRef<HTMLDivElement | null>(null)

  const viewerInstance = useRef<PdfViewerType | null>(null)
  const eventBus = useRef<EventBusType | null>(null)
  const linkService = useRef<SimpleLinkServiceType | null>(null)
  const findController = useRef<InstanceType<PdfModule['PDFFindController']> | null>(null)
  const findStates = useRef<PdfModule['FindState'] | null>(null)
  const scrollModes = useRef<ScrollModeEnum | null>(null)
  const spreadModes = useRef<SpreadModeEnum | null>(null)
  const pdfDoc = useRef<import('pdfjs-dist').PDFDocumentProxy | null>(null)

  const [phase, setPhase] = useState<'chargement' | 'pret' | 'erreur'>('chargement')
  const [erreur, setErreur] = useState('')
  const [pagesCount, setPagesCount] = useState(0)
  const [page, setPage] = useState(1)
  const [zoom, setZoom] = useState(0)
  const [sidebar, setSidebar] = useState(false)
  const [findOpen, setFindOpen] = useState(false)
  const [findQuery, setFindQuery] = useState('')
  const [findIndex, setFindIndex] = useState(0)
  const [findTotal, setFindTotal] = useState(0)
  const [findStatus, setFindStatus] = useState<'idle' | 'trouve' | 'introuvable'>('idle')
  const printed = useRef(false)
  const [printActif, setPrintActif] = useState(false)
  const [fullscreen, setFullscreen] = useState(false)
  const [thumbs, setThumbs] = useState<string[] | null>(null)
  const debounceFind = useRef<number | null>(null)
  const [modeDefilement, setModeDefilement] = useState<number | null>(null)
  const [etalage, setEtalage] = useState<number>(0)

  useEffect(() => {
    let cancelled = false
    let docASupprimer: import('pdfjs-dist').PDFDocumentProxy | null = null
    const vEl = viewerRef.current
    const sEl = scrollerRef.current
    setPhase('chargement')
    setErreur('')
    setPagesCount(0)
    setPage(1)

    ;(async () => {
      try {
        const pdfjs = await import('pdfjs-dist')
        if (cancelled) return
        ;(globalThis as { pdfjsLib?: typeof pdfjs }).pdfjsLib = pdfjs
        pdfjs.GlobalWorkerOptions.workerSrc = pdfWorkerUrl

        const mod = await chargerModule()
        if (cancelled) return
        scrollModes.current = mod.ScrollMode
        spreadModes.current = mod.SpreadMode
        findStates.current = mod.FindState
        const bus = new mod.EventBus()
        eventBus.current = bus
        const ls = new mod.SimpleLinkService()
        linkService.current = ls
        const fc = new mod.PDFFindController({ eventBus: bus, linkService: ls })
        findController.current = fc

        const doc = await pdfjs.getDocument({ data: new Uint8Array(data.slice(0)) }).promise
        if (cancelled) { void doc.destroy(); return }
        pdfDoc.current = doc
        docASupprimer = doc

        if (!sEl || !vEl) return
        const viewer = new mod.PDFViewer({
          container: sEl,
          viewer: vEl,
          eventBus: bus,
          linkService: ls,
          findController: fc,
        })
        viewerInstance.current = viewer
        viewer.setDocument(doc)
        ls.setDocument(doc)

        bus.on('pagechanging', ({ pageNumber }: { pageNumber: number }) => {
          setPage(pageNumber)
        })
        bus.on('scalechanging', ({ scale }: { scale: number }) => {
          setZoom(Math.round(scale * 100))
        })
        const majCompte = ({ matchesCount }: { matchesCount?: { current: number; total: number } }) => {
          if (!matchesCount) return
          setFindIndex(matchesCount.current)
          setFindTotal(matchesCount.total)
          setFindStatus(matchesCount.total > 0 ? 'trouve' : 'introuvable')
        }
        bus.on('updatefindcontrolstate', majCompte as never)
        bus.on('updatefindmatchescount', majCompte as never)
        bus.on('scrollmodechanged', ({ scrollMode }: { scrollMode: number }) => setModeDefilement(scrollMode))
        bus.on('spreadmodechanged', ({ spreadMode }: { spreadMode: number }) => setEtalage(spreadMode))

        setPagesCount(doc.numPages)
        viewer.currentScaleValue = 'page-width'
        viewer.scrollMode = initialScroll === 'horizontal' ? mod.ScrollMode.HORIZONTAL : mod.ScrollMode.VERTICAL
        setModeDefilement(viewer.scrollMode)
        setEtalage(viewer.spreadMode)
        setZoom(Math.round(viewer.currentScale * 100))
        setPhase('pret')
      } catch (err) {
        if (cancelled) return
        // eslint-disable-next-line no-console
        console.error('PdfViewerModal : échec du chargement', err)
        setErreur(err instanceof Error ? err.message : String(err))
        setPhase('erreur')
      }
    })()

    return () => {
      cancelled = true
      if (docASupprimer) void docASupprimer.destroy()
      viewerInstance.current = null
      if (vEl) vEl.innerHTML = ''
      const host = document.getElementById('pdfv-print-host')
      if (host) host.replaceChildren()
    }
  }, [data, initialScroll])

  useEffect(() => {
    const majFullscreen = () => setFullscreen(!!document.fullscreenElement)
    document.addEventListener('fullscreenchange', majFullscreen)
    return () => document.removeEventListener('fullscreenchange', majFullscreen)
  }, [])

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement
      const saisie = target instanceof HTMLInputElement || target instanceof HTMLTextAreaElement || target.isContentEditable
      if (e.key === 'Escape') {
        if (findOpen && saisie) {
          setFindOpen(false)
          eventBus.current?.dispatch('findbarclose', {})
          return
        }
        onClose()
        return
      }
      if (saisie) return
      if (e.key === 'PageUp' || e.key === 'ArrowLeft') naviguer(-1)
      else if (e.key === 'PageDown' || e.key === 'ArrowRight') naviguer(1)
      else if (e.key === 'f' && (e.ctrlKey || e.metaKey)) {
        e.preventDefault()
        setFindOpen(true)
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  })

  const naviguer = (delta: number) => {
    const v = viewerInstance.current
    if (!v) return
    const next = Math.min(Math.max(1, v.currentPageNumber + delta), v.pagesCount)
    v.currentPageNumber = next
  }

  const changerPage = (n: number) => {
    const v = viewerInstance.current
    if (v) v.currentPageNumber = Math.min(Math.max(1, n), v.pagesCount)
  }

  const zoomer = (sens: 1 | -1) => {
    const v = viewerInstance.current
    if (!v) return
    const actuel = v.currentScale
    const suivant = sens === 1
      ? PRESETS.find((p) => p > actuel + 0.001) ?? PRESETS[PRESETS.length - 1]
      : [...PRESETS].reverse().find((p) => p < actuel - 0.001) ?? PRESETS[0]
    v.currentScale = suivant
  }

  const ajuster = (valeur: string) => {
    if (viewerInstance.current) viewerInstance.current.currentScaleValue = valeur
  }

  const basculerScroll = () => {
    const v = viewerInstance.current
    const m = scrollModes.current
    if (!v || !m) return
    const ordre: number[] = [m.VERTICAL, m.HORIZONTAL, m.WRAPPED]
    const suivant = ordre[(ordre.indexOf(v.scrollMode) + 1) % ordre.length] as number
    v.scrollMode = suivant
  }

  const basculerEtalage = () => {
    const v = viewerInstance.current
    const m = spreadModes.current
    if (!v || !m) return
    v.spreadMode = v.spreadMode === m.NONE ? m.ODD : m.NONE
  }

  const lancerRecherche = (precedent = false) => {
    eventBus.current?.dispatch('find', {
      type: '',
      query: findQuery,
      caseSensitive: false,
      entireWord: false,
      matchDiacritics: false,
      findPrevious: precedent,
    })
  }

  const fermerRecherche = () => {
    setFindOpen(false)
    setFindQuery('')
    setFindIndex(0)
    setFindTotal(0)
    setFindStatus('idle')
    eventBus.current?.dispatch('findbarclose', {})
  }

  const basculerPleinEcran = async () => {
    try {
      if (document.fullscreenElement) {
        await document.exitFullscreen()
      } else {
        await rootRef.current?.requestFullscreen()
      }
    } catch {
      /* Plein écran refusé : on continue */
    }
  }

  const imprimer = async () => {
    const doc = pdfDoc.current
    if (!doc || printed.current) return
    printed.current = true
    setPrintActif(true)
    const host = getPrintHost()
    host.replaceChildren()
    try {
      for (let n = 1; n <= doc.numPages; n++) {
        const page = await doc.getPage(n)
        const base = page.getViewport({ scale: 1 })
        const paysage = base.width > base.height
        const targetWidth = Math.round(base.width * 1.5)
        const zoomImpression = targetWidth / base.width
        const viewport = page.getViewport({
          scale: zoomImpression,
          rotation: paysage ? (base.rotation + 90) % 360 : base.rotation,
        })
        const ratio = Math.min(window.devicePixelRatio || 1, 2)
        const canvas = document.createElement('canvas')
        canvas.width = Math.floor(viewport.width * ratio)
        canvas.height = Math.floor(viewport.height * ratio)
        canvas.style.width = `${Math.floor(viewport.width)}px`
        canvas.style.height = `${Math.floor(viewport.height)}px`
        const ctx = canvas.getContext('2d')
        if (!ctx) continue
        await page.render({
          canvasContext: ctx,
          viewport,
          transform: ratio !== 1 ? [ratio, 0, 0, ratio, 0, 0] : undefined,
        }).promise
        const div = document.createElement('div')
        div.className = 'pdfv-print-page'
        div.appendChild(canvas)
        host.appendChild(div)
      }
      window.print()
    } finally {
      host.replaceChildren()
      printed.current = false
      setPrintActif(false)
    }
  }

  useEffect(() => {
    if (phase !== 'pret' || !impressionAuto) return
    const timer = window.setTimeout(() => {
      void imprimer().finally(() => onImpressionAutoFini?.())
    }, 550)
    return () => window.clearTimeout(timer)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [phase, impressionAuto])

  useEffect(() => {
    const doc = pdfDoc.current
    if (!sidebar || !doc || thumbs) return
    let cancelled = false
    ;(async () => {
      const sortie: string[] = []
      for (let n = 1; n <= doc.numPages; n++) {
        if (cancelled) return
        try {
          const page = await doc.getPage(n)
          const base = page.getViewport({ scale: 1 })
          const scale = 130 / base.width
          const viewport = page.getViewport({ scale })
          const canvas = document.createElement('canvas')
          canvas.width = Math.max(1, Math.floor(viewport.width))
          canvas.height = Math.max(1, Math.floor(viewport.height))
          const ctx = canvas.getContext('2d')
          if (ctx) await page.render({ canvasContext: ctx, viewport }).promise
          sortie.push(canvas.toDataURL('image/jpeg', 0.85))
        } catch {
          sortie.push('')
        }
      }
      if (!cancelled) setThumbs(sortie)
    })()
    return () => {
      cancelled = true
    }
  }, [sidebar, thumbs])

  return (
    <div ref={rootRef} className={fullscreen ? 'pdfv-root pdfv-fullscreen' : 'pdfv-root'}>
      <div className="pdfv-chrome no-print">
        <div className="pdfv-title">
          <FileWarning size={15} strokeWidth={1.75} className="shrink-0 text-[var(--ink-faint)]" />
          <span title={filename}>{filename}</span>
        </div>

        {phase === 'pret' && pagesCount > 1 && (
          <div className="pdfv-page-indicator">
            <Tooltip content="Page précédente">
            <button className="pdfv-icon-btn" onClick={() => naviguer(-1)} disabled={page <= 1} aria-label="Page précédente">
              <ChevronLeft size={15} strokeWidth={1.75} />
            </button>
            </Tooltip>
            <b>{page}</b>
            <span>/</span>
            <span>{pagesCount}</span>
            <Tooltip content="Page suivante">
            <button className="pdfv-icon-btn" onClick={() => naviguer(1)} disabled={page >= pagesCount} aria-label="Page suivante">
              <ChevronRight size={15} strokeWidth={1.75} />
            </button>
            </Tooltip>
          </div>
        )}

        <div className="pdfv-sep" />

        {phase === 'pret' && (
          <Tooltip content="Zoom arrière">
          <button className="pdfv-icon-btn" onClick={() => zoomer(-1)} disabled={zoom <= Math.round(PRESETS[0] * 100)} aria-label="Zoom arrière">
            <ZoomOut size={15} strokeWidth={1.75} />
          </button>
          </Tooltip>
        )}
        <span className="pdfv-zoom-display">{zoom > 0 ? `${zoom} %` : ''}</span>
        {phase === 'pret' && (
          <Tooltip content="Zoom avant">
          <button className="pdfv-icon-btn" onClick={() => zoomer(1)} aria-label="Zoom avant">
            <ZoomIn size={15} strokeWidth={1.75} />
          </button>
          </Tooltip>
        )}

        {phase === 'pret' && (
          <button className="pdfv-tool-btn" onClick={() => ajuster('page-width')}>
            Largeur
          </button>
        )}
        {phase === 'pret' && (
          <button className="pdfv-tool-btn" onClick={() => ajuster('page-fit')}>
            Page
          </button>
        )}

        <div className="pdfv-sep" />

        {phase === 'pret' && (
          <button
            className="pdfv-tool-btn"
            onClick={basculerScroll}
          >
            {modeDefilement === scrollModes.current?.HORIZONTAL ? <Rows3 size={13} strokeWidth={1.75} /> : <Columns2 size={13} strokeWidth={1.75} />}
            Défilement
          </button>
        )}
        {phase === 'pret' && (
          <button
            className={modeDefilement !== scrollModes.current?.VERTICAL && etalage !== 0 ? 'pdfv-tool-btn pdfv-active' : 'pdfv-tool-btn'}
            onClick={basculerEtalage}
          >
            <SpellCheck2 size={13} strokeWidth={1.75} />
            Vis-à-vis
          </button>
        )}
        {phase === 'pret' && (
          <button
            className={sidebar ? 'pdfv-tool-btn pdfv-active' : 'pdfv-tool-btn'}
            onClick={() => setSidebar((s) => !s)}
          >
            <LayoutPanelLeft size={13} strokeWidth={1.75} />
            Miniatures
          </button>
        )}
        {phase === 'pret' && (
          <button
            className={findOpen ? 'pdfv-tool-btn pdfv-active' : 'pdfv-tool-btn'}
            onClick={() => (findOpen ? fermerRecherche() : setFindOpen(true))}
          >
            <Search size={13} strokeWidth={1.75} />
            Rechercher
          </button>
        )}

        <div className="pdfv-sep" />

        {phase === 'pret' && (
          <Tooltip content="Imprimer ce document">
          <button className="pdfv-icon-btn" onClick={imprimer} disabled={printActif} aria-label="Imprimer">
            <Printer size={15} strokeWidth={1.75} />
          </button>
          </Tooltip>
        )}
        {onDownload && (
          <Button variant="secondary" size="sm" isLoading={downloading} onClick={onDownload} disabled={phase === 'chargement'}>
            <Download size={13} strokeWidth={1.75} className="mr-1.5" />
            Télécharger
          </Button>
        )}
        <Tooltip content={fullscreen ? 'Quitter le plein écran' : 'Plein écran'}>
        <button className="pdfv-icon-btn" onClick={basculerPleinEcran} aria-label="Plein écran">
          {fullscreen ? <Minimize2 size={15} strokeWidth={1.75} /> : <Maximize2 size={15} strokeWidth={1.75} />}
        </button>
        </Tooltip>
        <Tooltip content="Fermer (Échap)">
        <button className="pdfv-icon-btn" onClick={onClose} aria-label="Fermer">
          <X size={16} strokeWidth={1.75} />
        </button>
        </Tooltip>
      </div>

      <div className={sidebar ? 'pdfv-main no-print pdfv-sidebar-open' : 'pdfv-main no-print'}>
        {sidebar && phase === 'pret' && (
          <div className="pdfv-sidebar">
            <div className="pdfv-sidebar-head">Pages</div>
            <div className="pdfv-thumbs">
              {thumbs ? (
                thumbs.map((src, i) => (
                  <button
                    key={i}
                    className={i + 1 === page ? 'pdfv-thumb pdfv-current' : 'pdfv-thumb'}
                    onClick={() => changerPage(i + 1)}
                    title={`Aller à la page ${i + 1}`}
                  >
                    {src ? (
                      <>
                        <img src={src} alt={`Miniature page ${i + 1}`} />
                        <span className="pdfv-thumb-label">{i + 1}</span>
                      </>
                    ) : (
                      <span className="pdfv-thumb-loading">{i + 1}</span>
                    )}
                  </button>
                ))
              ) : (
                <div className="pdfv-thumb-loading">
                  <Spinner label="Miniatures…" />
                </div>
              )}
            </div>
          </div>
        )}

        {phase === 'chargement' && (
          <div className="pdfv-center">
            <div className="pdfv-loading">
              <Spinner label="Chargement du document…" />
            </div>
          </div>
        )}
        {phase === 'erreur' && (
          <div className="pdfv-center">
            <FileWarning size={34} strokeWidth={1.5} className="text-[var(--ink-faint)]" />
            <span className="pdfv-error">Impossible d'afficher ce PDF.</span>
            <span className="max-w-sm text-center text-xs">{erreur}</span>
            {onDownload && (
              <Button variant="primary" size="sm" onClick={onDownload}>
                <Download size={13} strokeWidth={1.75} className="mr-1.5" />
                Télécharger le fichier
              </Button>
            )}
          </div>
        )}

        <div ref={scrollerRef} className="pdfv-scroller" tabIndex={0}>
          <div ref={viewerRef} className="pdfViewer" />
        </div>

        {findOpen && phase === 'pret' && (
          <div className="pdfv-findbar">
            <input
              autoFocus
              value={findQuery}
              placeholder="Rechercher…"
              onChange={(e) => {
                const valeur = e.target.value
                setFindQuery(valeur)
                if (debounceFind.current) window.clearTimeout(debounceFind.current)
                debounceFind.current = window.setTimeout(() => {
                  eventBus.current?.dispatch('find', {
                    type: '',
                    query: valeur,
                    caseSensitive: false,
                    entireWord: false,
                    matchDiacritics: false,
                    findPrevious: false,
                  })
                }, 150)
              }}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault()
                  lancerRecherche(e.shiftKey)
                }
              }}
            />
            <span className={findStatus === 'introuvable' ? 'pdfv-find-count pdfv-empty' : 'pdfv-find-count'}>
              {findTotal > 0 ? `${findIndex} / ${findTotal}` : findQuery ? '0' : ''}
            </span>
            <Tooltip content="Précédent (Maj+Entrée)">
            <button className="pdfv-icon-btn" onClick={() => lancerRecherche(true)} aria-label="Occurrence précédente">
              <ChevronLeft size={14} strokeWidth={1.75} />
            </button>
            </Tooltip>
            <Tooltip content="Suivant (Entrée)">
            <button className="pdfv-icon-btn" onClick={() => lancerRecherche(false)} aria-label="Occurrence suivante">
              <ChevronRight size={14} strokeWidth={1.75} />
            </button>
            </Tooltip>
            <Tooltip content="Fermer la recherche">
            <button className="pdfv-icon-btn" onClick={fermerRecherche} aria-label="Fermer la recherche">
              <X size={14} strokeWidth={1.75} />
            </button>
            </Tooltip>
          </div>
        )}
      </div>
    </div>
  )
}