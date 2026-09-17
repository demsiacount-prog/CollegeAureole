import { useMemo, useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import {
  File,
  FileText,
  Files,
  FolderOpen,
  GraduationCap,
  HeartPulse,
  IdCard,
  Image,
  LayoutGrid,
  List as ListIcon,
  Plus,
  Search,
} from 'lucide-react'
import { Button, IconButton } from '@/components/ui/Button'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { EmptyState } from '@/components/ui/EmptyState'
import { Input } from '@/components/ui/Input'
import { toast } from '@/components/ui/toast'
import { Tooltip } from '@/components/ui/Tooltip'
import { extractErrorMessage } from '@/lib/api'
import { scheduleDeleteWithUndo } from '@/lib/undoDelete'
import { clsx } from 'clsx'
import { deleteDocument, downloadBlob, fetchDocumentBlob, documentsQueryKey } from './api'
import { useDocuments, useUploadDocument } from './hooks'
import { DOC_CATEGORIES, DOC_CATEGORY_ORDER } from './labels'
import { DocumentGrid } from './DocumentGrid'
import { DocumentList } from './DocumentList'
import { DocumentViewer } from './DocumentViewer'
import { UploadDrawer } from './UploadDrawer'
import { UploadZone } from './UploadZone'
import type { DocumentCategorieKey, DocumentRead, EntiteDocument } from './types'

interface DocumentsTabProps {
  entiteType: EntiteDocument
  entiteId: string
  readOnly?: boolean
}

const CATEGORY_ICONS: Record<DocumentCategorieKey, typeof File> = {
  identite: IdCard,
  photo: Image,
  naissance: FileText,
  scolaire: GraduationCap,
  medical: HeartPulse,
  administratif: FolderOpen,
  autre: File,
}

/** Onglet Documents des dossiers (Type K + visionneuse Type L).
 *  Charge ses propres données via la clé de cache `['documents', type, id]`
 *  partagée avec les pages (le compteur d'onglet ne provoque pas de 2ᵉ requête). */
export function DocumentsTab({ entiteType, entiteId, readOnly = false }: DocumentsTabProps) {
  const qc = useQueryClient()
  const { data: docs = [], isLoading } = useDocuments(entiteType, entiteId)

  const [view, setView] = useState<'grid' | 'list'>('grid')
  const [search, setSearch] = useState('')
  const [uploadOpen, setUploadOpen] = useState(false)
  const [pendingFile, setPendingFile] = useState<File | null>(null)
  const [deleting, setDeleting] = useState<DocumentRead | null>(null)
  const [apercu, setApercu] = useState<DocumentRead | null>(null)

  const uploadMut = useUploadDocument(entiteType, entiteId)

  const deleteMut = useMutation({
    mutationFn: deleteDocument,
    onSuccess: () => {
      toast('Document supprimé')
      qc.invalidateQueries({ queryKey: documentsQueryKey(entiteType, entiteId) })
    },
    onError: (e) => toast(extractErrorMessage(e), 'error'),
  })

  const montrerRecherche = docs.length > 5

  const filtrees = useMemo(() => {
    if (!search.trim()) return docs
    const q = search.trim().toLowerCase()
    return docs.filter((d) => d.nom.toLowerCase().includes(q))
  }, [docs, search])

  const groupes = useMemo(() => {
    const g: Record<string, DocumentRead[]> = {}
    for (const doc of filtrees) {
      ;(g[doc.categorie] ??= []).push(doc)
    }
    return g
  }, [filtrees])

  function ouvrirUpload(fichier?: File) {
    setPendingFile(fichier ?? null)
    setUploadOpen(true)
  }

  function debuterSuppression(doc: DocumentRead) {
    setDeleting(doc)
  }

  async function telecharger(doc: DocumentRead) {
    downloadBlob(await fetchDocumentBlob(doc.id), doc.nom)
  }

  function confirmerSuppression() {
    if (!deleting) return
    const id = deleting.id
    setDeleting(null)
    scheduleDeleteWithUndo(() => deleteMut.mutate(id), 'Document supprimé.')
  }

  return (
    <div className="viewer-shell">
      <div className="viewer-main">
        <div className="doc-toolbar">
          {!readOnly && (
            <Button variant="primary" size="sm" onClick={() => ouvrirUpload()}>
              <Plus size={13} strokeWidth={2} />
              Ajouter un document
            </Button>
          )}
          <span className="flex-1" />
          {montrerRecherche && (
            <div className="relative w-[200px]">
              <div className="pointer-events-none absolute left-[9px] top-1/2 -translate-y-1/2 text-[var(--ink-faint)]">
                <Search size={13} strokeWidth={2} />
              </div>
              <Input
                aria-label="Rechercher un document"
                placeholder="Rechercher…"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="h-[28px] pl-[28px] text-[12px]"
              />
            </div>
          )}
          <div className="flex items-center gap-[2px] rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-2)] p-[2px]">
            <Tooltip content="Vue grille">
              <IconButton
                size="sm"
                aria-label="Vue grille"
                onClick={() => setView('grid')}
                className={clsx(
                  '!size-[22px] rounded-[var(--radius-sm)]',
                  view === 'grid' ? '!text-[var(--halo)] !bg-[var(--halo-wash)]' : '',
                )}
              >
                <LayoutGrid size={13} strokeWidth={2} />
              </IconButton>
            </Tooltip>
            <Tooltip content="Vue liste">
              <IconButton
                size="sm"
                aria-label="Vue liste"
                onClick={() => setView('list')}
                className={clsx(
                  '!size-[22px] rounded-[var(--radius-sm)]',
                  view === 'list' ? '!text-[var(--halo)] !bg-[var(--halo-wash)]' : '',
                )}
              >
                <ListIcon size={13} strokeWidth={2} />
              </IconButton>
            </Tooltip>
          </div>
        </div>

        {isLoading ? (
          <div className="grid grid-cols-[repeat(auto-fill,minmax(160px,1fr))] gap-3 pt-1">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="overflow-hidden rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--surface)]">
                <div className="skeleton h-[100px] rounded-none" />
                <div className="p-[9px_10px]">
                  <div className="skeleton h-[12px] w-4/5 rounded-[3px]" />
                  <div className="mt-[6px] flex justify-between">
                    <div className="skeleton h-[10px] w-1/3" />
                    <div className="skeleton h-[10px] w-1/4" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : filtrees.length === 0 ? (
          <EmptyState
            icon={Files}
            title={montrerRecherche ? 'Aucun résultat' : 'Aucun document'}
            message={
              montrerRecherche
                ? 'Aucune pièce ne correspond à votre recherche.'
                : 'Aucune pièce jointe pour ce dossier.'
            }
            action={
              !readOnly && !montrerRecherche ? (
                <Button variant="primary" size="sm" onClick={() => ouvrirUpload()}>
                  <Plus size={13} strokeWidth={2} />
                  Ajouter un document
                </Button>
              ) : undefined
            }
          />
        ) : (
          <>
            {DOC_CATEGORY_ORDER.map((cat) => {
              const catDocs = groupes[cat]
              if (!catDocs || catDocs.length === 0) return null
              const Icon = CATEGORY_ICONS[cat]
              return (
                <div key={cat} className="doc-category-section">
                  <div className="doc-category-title">
                    <Icon size={13} strokeWidth={1.75} />
                    {DOC_CATEGORIES[cat]}
                    <span className="doc-category-count">{catDocs.length}</span>
                  </div>
                  {view === 'grid' ? (
                    <DocumentGrid
                      docs={catDocs}
                      onPreview={setApercu}
                      onDownload={(d) => void telecharger(d)}
                      onDelete={readOnly ? undefined : debuterSuppression}
                    />
                  ) : (
                    <DocumentList
                      docs={catDocs}
                      onPreview={setApercu}
                      onDownload={(d) => void telecharger(d)}
                      onDelete={readOnly ? undefined : debuterSuppression}
                    />
                  )}
                </div>
              )
            })}
            {!readOnly && (
              <UploadZone onSelect={(file) => ouvrirUpload(file)} />
            )}
          </>
        )}
      </div>

      {apercu && (
        <DocumentViewer
          doc={apercu}
          onClose={() => setApercu(null)}
          onOpenUpload={readOnly ? undefined : () => ouvrirUpload()}
        />
      )}

      <UploadDrawer
        open={uploadOpen}
        initialFile={pendingFile}
        onClose={() => setUploadOpen(false)}
        isLoading={uploadMut.isPending}
        onSubmit={(payload) =>
          uploadMut.mutate(payload, {
            onSuccess: () => {
              toast('Document importé')
              setUploadOpen(false)
            },
            onError: (e) => toast(extractErrorMessage(e), 'error'),
          })
        }
      />

      <ConfirmDialog
        open={!!deleting}
        onClose={() => setDeleting(null)}
        onConfirm={confirmerSuppression}
        title="Supprimer ce document ?"
        description={`Supprimer ${deleting ? `« ${deleting.nom} »` : 'ce document'} ?`}
        confirmLabel="Supprimer"
        variant="danger"
      />
    </div>
  )
}