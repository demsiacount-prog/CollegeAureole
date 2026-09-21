import { useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Archive, FileSpreadsheet, FileUp, RefreshCw, Trash2, UploadCloud } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { Card } from '@/components/ui/Card'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { EmptyState } from '@/components/ui/EmptyState'
import { toast } from '@/components/ui/toast'
import { extractErrorMessage } from '@/lib/api'
import {
  creerSauvegardeServeur,
  fetchSauvegardesServeur,
  formaterTaille,
  importerSauvegarde,
  telechargerExportExcel,
  telechargerSauvegardeComplete,
} from './sauvegardesApi'

/** Onglet Paramètres → Export : sauvegarde complète (ZIP), export Excel,
 *  sauvegardes serveur et restauration symétrique (import). */
export default function ExportTab() {
  const qc = useQueryClient()
  const { data: sauvegardes = [], isFetching } = useQuery({
    queryKey: ['sauvegardes'],
    queryFn: fetchSauvegardesServeur,
  })

  const [download, setDownload] = useState<'xlsx' | 'zip' | null>(null)
  const [fichier, setFichier] = useState<File | null>(null)
  const [confirmImportOpen, setConfirmImportOpen] = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)

  const handleTelecharger = (type: 'xlsx' | 'zip') => async () => {
    setDownload(type)
    try {
      if (type === 'xlsx') await telechargerExportExcel()
      else await telechargerSauvegardeComplete()
      toast(type === 'xlsx' ? 'Export Excel téléchargé.' : 'Sauvegarde complète téléchargée.')
    } catch (e) {
      toast(extractErrorMessage(e, 'Erreur lors du téléchargement.'), 'error')
    } finally {
      setDownload(null)
    }
  }

  const creerMut = useMutation({
    mutationFn: creerSauvegardeServeur,
    onSuccess: (nom) => {
      toast(`Sauvegarde serveur créée : ${nom}`)
      qc.invalidateQueries({ queryKey: ['sauvegardes'] })
    },
    onError: (e) => toast(extractErrorMessage(e), 'error'),
  })

  const importMut = useMutation({
    mutationFn: () => importerSauvegarde(fichier!),
    onSuccess: (r) => {
      toast(`Restauration terminée : ${r.lignes_importees} lignes importées.`)
      setConfirmImportOpen(false)
      setFichier(null)
      qc.invalidateQueries()
    },
    onError: (e) => {
      toast(extractErrorMessage(e), 'error')
      setConfirmImportOpen(false)
    },
  })

  return (
    <div className="space-y-6">
      <h3 className="mb-4 border-b border-[var(--border-soft)] pb-2 text-sm font-semibold text-[var(--ink)]">
        Export, sauvegardes et restauration
      </h3>

      {/* ── Téléchargements ──────────────────────────────────────────────── */}
      <div className="space-y-3">
        <Card className="p-5">
          <div className="flex items-start justify-between gap-4">
            <div className="flex items-start gap-3">
              <Archive size={18} strokeWidth={1.75} className="mt-0.5 shrink-0 text-[var(--action)]" />
              <div>
                <p className="text-sm font-medium text-[var(--ink)]">Sauvegarde complète (.zip)</p>
                <p className="mt-0.5 text-xs text-[var(--ink-dim)]">
                  Archive recommandée : toutes les tables, le contenu des pièces jointes et les fichiers
                  téléversés (uploads). C&apos;est le format attendu par la restauration.
                </p>
              </div>
            </div>
            <Button
              variant="primary"
              isLoading={download === 'zip'}
              onClick={handleTelecharger('zip')}
              className="shrink-0"
            >
              Télécharger la sauvegarde
            </Button>
          </div>
        </Card>

        <Card className="p-5">
          <div className="flex items-start justify-between gap-4">
            <div className="flex items-start gap-3">
              <FileSpreadsheet size={18} strokeWidth={1.75} className="mt-0.5 shrink-0 text-[var(--action)]" />
              <div>
                <p className="text-sm font-medium text-[var(--ink)]">Export Excel (.xlsx)</p>
                <p className="mt-0.5 text-xs text-[var(--ink-dim)]">
                  Classeur simple en lecture : un onglet par table, sans le contenu binaire des documents.
                  Pour une vraie sauvegarde, utilisez le format .zip ci-dessus.
                </p>
              </div>
            </div>
            <Button variant="secondary" isLoading={download === 'xlsx'} onClick={handleTelecharger('xlsx')} className="shrink-0">
              Télécharger l&apos;export
            </Button>
          </div>
        </Card>
      </div>

      {/* ── Sauvegardes sur le serveur ───────────────────────────────────── */}
      <Card>
        <div className="flex items-center justify-between p-5 pb-3">
          <div className="flex items-center gap-3">
            <UploadCloud size={18} strokeWidth={1.75} className="mt-0.5 shrink-0 text-[var(--action)]" />
            <div>
              <p className="text-sm font-medium text-[var(--ink)]">Sauvegardes sur le serveur</p>
              <p className="mt-0.5 text-xs text-[var(--ink-dim)]">
                Archives conservées dans sauvegardes/ avec rotation automatique. Elles ne remplacent pas un
                export téléchargé sur un support externe.
              </p>
            </div>
          </div>
          <div className="flex shrink-0 gap-2">
            <Button variant="ghost" size="sm" isLoading={isFetching} onClick={() => qc.invalidateQueries({ queryKey: ['sauvegardes'] })}>
              <RefreshCw size={14} strokeWidth={1.75} className="mr-1" />
              Actualiser
            </Button>
            <Button variant="primary" size="sm" isLoading={creerMut.isPending} onClick={() => creerMut.mutate()}>
              Créer une sauvegarde
            </Button>
          </div>
        </div>
        {sauvegardes.length === 0 ? (
          <div className="p-5 pt-0">
            <EmptyState message="Aucune sauvegarde sur le serveur pour le moment." />
          </div>
        ) : (
          <div className="px-5 pb-5">
            <div className="divide-y divide-[var(--border-soft)] rounded-[var(--radius-md)] border border-[var(--border)]">
              {sauvegardes.map((s) => (
                <div key={s.nom} className="flex items-center justify-between gap-3 px-4 py-2.5">
                  <span className="truncate text-[13px] text-[var(--ink)]">{s.nom}</span>
                  <div className="flex shrink-0 items-center gap-3 text-xs text-[var(--ink-faint)]">
                    <span>{formaterTaille(s.taille_octets)}</span>
                    <span>{new Date(s.cree_le).toLocaleString('fr-FR')}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </Card>

      {/* ── Restauration (import) ────────────────────────────────────────── */}
      <Card className="p-5">
        <div className="mb-4 flex items-start gap-3">
          <Trash2 size={18} strokeWidth={1.75} className="mt-0.5 shrink-0 text-[var(--danger)]" />
          <div>
            <p className="text-sm font-medium text-[var(--ink)]">Restaurer une sauvegarde</p>
            <p className="mt-0.5 text-xs text-[var(--ink-dim)]">
              Rétablissez l&apos;intégralité des données depuis une sauvegarde .zip. Le contenu actuel est
              <Badge tone="danger" className="mx-1">remplacé intégralement</Badge>, après enregistrement
              automatique d&apos;un snapshot de sécurité de la base actuelle.
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <input
            ref={fileRef}
            type="file"
            accept=".zip,application/zip"
            className="hidden"
            onChange={(e) => setFichier(e.target.files?.[0] ?? null)}
          />
          <Button variant="secondary" onClick={() => fileRef.current?.click()}>
            <FileUp size={16} strokeWidth={1.75} className="mr-1.5" />
            {fichier ? 'Changer de fichier…' : 'Choisir une sauvegarde (.zip)'}
          </Button>
          {fichier && (
            <span className="text-[12.5px] text-[var(--ink-dim)]">
              {fichier.name}{' '}
              <span className="text-[var(--ink-faint)]">({formaterTaille(fichier.size)})</span>
            </span>
          )}
          <Button
            variant="danger"
            className="ml-auto"
            disabled={!fichier}
            onClick={() => setConfirmImportOpen(true)}
          >
            Restaurer cette sauvegarde…
          </Button>
        </div>
      </Card>

      <ConfirmDialog
        open={confirmImportOpen}
        onClose={() => setConfirmImportOpen(false)}
        onConfirm={() => importMut.mutate()}
        isLoading={importMut.isPending}
        title="Restaurer cette sauvegarde ?"
        description={`Toutes les données actuelles seront REMPLACÉES par le contenu de « ${fichier?.name} ». Un snapshot de sécurité de la base actuelle est créé automatiquement avant la restauration. Cette action est irréversible.`}
        confirmLabel="Restaurer définitivement"
        variant="danger"
      />
    </div>
  )
}