import { useRef, useState } from 'react'
import { AlertCircle, Download, Eye, FileText, Upload } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { Card } from '@/components/ui/Card'
import { toast } from '@/components/ui/toast'
import { extractErrorMessage } from '@/lib/api'
import { formatDate } from '@/lib/format'
import { useDocuments, useUploadDocument } from '@/features/documents/hooks'
import { deleteDocument, downloadBlob, fetchDocumentBlob } from '@/features/documents/api'
import { DocumentViewer } from '@/features/documents/DocumentViewer'
import type { DocumentRead } from '@/features/documents/types'
import type { DossierEleve } from './types'

/** Pièces clés du dossier (onglet Profil) — acte de naissance (état civil +
 *  scan consultable/importable). Le carnet scolaire (PDF officiel) n'est plus
 *  généré : la scolarité se consulte par les bulletins et relevés de notes.
 *  Source de vérité unique : clé de cache partagée `['documents', 'eleve', id]`
 *  avec l'onglet Documents. */
export function PiecesClesDossier({ dossier }: { dossier: DossierEleve }) {
  const matricule = dossier.matricule

  const { data: docs = [] } = useDocuments('eleve', matricule)
  const uploadMut = useUploadDocument('eleve', matricule)

  const [apercu, setApercu] = useState<DocumentRead | null>(null)
  const fileInputRef = useRef<HTMLInputElement | null>(null)
  const [uploading, setUploading] = useState(false)

  const acteDocs = docs.filter(
    (d) => d.categorie === 'naissance' || d.type_document === 'acte_naissance',
  )
  const acteDoc = acteDocs[0] ?? null
  const scanPresent = !!acteDoc

  async function telechargerActe() {
    if (!acteDoc) return
    downloadBlob(await fetchDocumentBlob(acteDoc.id), acteDoc.nom)
  }

  async function importerActe(file: File) {
    if (!file) return
    setUploading(true)
    try {
      const cree = await uploadMut.mutateAsync({
        fichier: file,
        nom: `Acte_naissance_${dossier.nom}_${dossier.prenom}`,
        categorie: 'naissance',
      })
      // Remplacer la pièce précédente : on supprime les anciens scans d'acte.
      const aSupprimer = acteDocs.filter((d) => d.id !== cree.id)
      for (const a of aSupprimer) {
        try {
          await deleteDocument(a.id)
        } catch {
          /* conservatoire : la pièce la plus récente fait foi */
        }
      }
      toast('Acte de naissance importé')
    } catch (err) {
      toast(extractErrorMessage(err, "Impossible d'importer l'acte de naissance."), 'error')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div>
      <div className="mb-[18px]">
        <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.08em] text-[var(--ink-faint)]">
          Pièces clés du dossier
        </p>

        <Card className="mb-4 p-4">
          <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-2.5">
              <span className="flex size-8 shrink-0 items-center justify-center rounded-[var(--radius-md)] bg-[var(--surface-2)]">
                <FileText size={15} strokeWidth={1.75} className="text-[var(--ink-dim)]" />
              </span>
              <div>
                <p className="text-[13px] font-semibold text-[var(--ink)]">Acte de naissance</p>
                <p className="text-[11px] text-[var(--ink-faint)]">État civil + pièce scannée</p>
              </div>
            </div>
            {scanPresent ? (
              <Badge tone="success">Présent</Badge>
            ) : (
              <Badge tone="warning">À compléter</Badge>
            )}
          </div>

          <div className="mb-4 grid grid-cols-1 gap-1.5 rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-2)] px-3 py-2.5 sm:grid-cols-2">
            <p className="text-[11.5px] text-[var(--ink)]">
              <span className="text-[var(--ink-faint)]">N° acte : </span>
              {dossier.numero_acte ?? '—'}
            </p>
            <p className="text-[11.5px] text-[var(--ink)]">
              <span className="text-[var(--ink-faint)]">Jugement supplétif : </span>
              {dossier.jugement_suppletif ?? '—'}
            </p>
            <p className="text-[11.5px] text-[var(--ink)]">
              <span className="text-[var(--ink-faint)]">Date de l'acte : </span>
              {dossier.date_acte ? formatDate(dossier.date_acte) : '—'}
            </p>
            <p className="text-[11.5px] text-[var(--ink)]">
              <span className="text-[var(--ink-faint)]">Délivré par : </span>
              {dossier.delivre_par ?? '—'}
            </p>
          </div>

          {acteDoc ? (
            <div className="flex flex-wrap items-center gap-2">
              <Button size="sm" variant="secondary" onClick={() => setApercu(acteDoc)}>
                <Eye size={13} strokeWidth={1.75} />
                Aperçu
              </Button>
              <Button size="sm" variant="secondary" onClick={() => void telechargerActe()}>
                <Download size={13} strokeWidth={1.75} />
                Télécharger
              </Button>
              <Button
                size="sm"
                variant="secondary"
                onClick={() => fileInputRef.current?.click()}
                isLoading={uploading}
              >
                <Upload size={13} strokeWidth={1.75} />
                Remplacer
              </Button>
            </div>
          ) : (
            <div className="flex flex-wrap items-center gap-2">
              <Button
                size="sm"
                variant="primary"
                onClick={() => fileInputRef.current?.click()}
                isLoading={uploading}
              >
                <Upload size={13} strokeWidth={1.75} />
                Importer l'acte
              </Button>
              <p className="flex items-center gap-1.5 text-[11px] text-[var(--ink-faint)]">
                <AlertCircle size={12} strokeWidth={1.75} />
                PDF, JPG ou PNG — 10 Mo max
              </p>
            </div>
          )}
        </Card>
      </div>

      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.jpg,.jpeg,.png"
        className="hidden"
        onChange={(e) => {
          const f = e.target.files?.[0] ?? null
          e.target.value = ''
          if (f) void importerActe(f)
        }}
      />

      {apercu && <DocumentViewer doc={apercu} onClose={() => setApercu(null)} />}
    </div>
  )
}