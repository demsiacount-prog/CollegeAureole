import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Download, KeyRound, Plus, Search, Trash2 } from 'lucide-react'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { EmptyState } from '@/components/ui/EmptyState'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { Table, TableBody, TableCell, TableContainer, TableHead, TableHeader, TableRow } from '@/components/ui/Table'
import { TableSkeleton } from '@/components/ui/TableSkeleton'
import { Tooltip } from '@/components/ui/Tooltip'
import { toast } from '@/components/ui/toast'
import { extractErrorMessage } from '@/lib/api'
import { useAuth } from '@/auth/useAuth'
import { AddDocumentDrawer } from './AddDocumentDrawer'
import {
  deleteDocument,
  downloadBlob,
  fetchDocumentBlob,
  fetchTousDocuments,
  uploadDocumentGenerique,
} from './api'
import { ALL_DOCS_LABELS, DOC_CATEGORIES, formatFileSize } from './labels'
import type { DocumentCategorieKey, DocumentRead, EntiteDocument } from './types'

const ENTITE_OPTIONS: { value: EntiteDocument; label: string }[] = [
  { value: 'eleve', label: 'Élève' },
  { value: 'enseignant', label: 'Enseignant' },
  { value: 'tuteur', label: 'Tuteur' },
]

/**
 * Onglet « Gestion documentaire » (Type K) : liste globale de l'API §46
 * (`GET /api/documents/`). Les écritures (upload/suppression) et la lecture des
 * documents médicaux sont réservées aux administrateurs — le backend renvoie
 * 403 sinon, et masque déjà les documents médicaux pour les autres rôles.
 */
export default function GestionDocumentaireTab() {
  const qc = useQueryClient()
  const { user } = useAuth()
  const estAdmin = (user?.role ?? '').trim().toUpperCase() === 'ADMIN'

  const { data: docs = [], isLoading, isError, error } = useQuery({
    queryKey: ['documents', 'tous'],
    queryFn: fetchTousDocuments,
  })

  const [search, setSearch] = useState('')
  const [uploadOpen, setUploadOpen] = useState(false)
  const [entiteType, setEntiteType] = useState<EntiteDocument>('eleve')
  const [entiteId, setEntiteId] = useState('')
  const [deleting, setDeleting] = useState<DocumentRead | null>(null)

  const uploadMut = useMutation({
    mutationFn: uploadDocumentGenerique,
    onSuccess: () => {
      toast('Document importé')
      qc.invalidateQueries({ queryKey: ['documents'] })
      setUploadOpen(false)
    },
    onError: (e) => toast(extractErrorMessage(e), 'error'),
  })

  const deleteMut = useMutation({
    mutationFn: deleteDocument,
    onSuccess: () => {
      toast('Document supprimé')
      qc.invalidateQueries({ queryKey: ['documents'] })
      setDeleting(null)
    },
    onError: (e) => toast(extractErrorMessage(e), 'error'),
  })

  const visibles = useMemo(() => {
    // Défense en profondeur : le backend masque déjà les documents médicaux
    // aux non-admins, on ne les affiche pas non plus côté client.
    const autorises = estAdmin ? docs : docs.filter((d) => d.categorie !== 'medical')
    const q = search.trim().toLowerCase()
    if (!q) return autorises
    return autorises.filter(
      (d) =>
        d.nom.toLowerCase().includes(q) ||
        (d.entite_label ?? '').toLowerCase().includes(q),
    )
  }, [docs, estAdmin, search])

  async function soumettre(typeDocument: string, file: File) {
    const identifiant = entiteId.trim()
    if (!identifiant) {
      toast("Renseignez l'identifiant de l'entité cible (matricule ou code).", 'error')
      throw new Error('entite_id manquant')
    }
    await uploadMut.mutateAsync({
      entiteType,
      entiteId: identifiant,
      fichier: file,
      categorie: typeDocument as DocumentCategorieKey,
    })
  }

  async function telecharger(doc: DocumentRead) {
    try {
      downloadBlob(await fetchDocumentBlob(doc.id), doc.nom)
    } catch (e) {
      toast(extractErrorMessage(e, 'Téléchargement impossible.'), 'error')
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="mb-4 border-b border-[var(--border-soft)] pb-2 text-sm font-semibold text-[var(--ink)]">
          Gestion documentaire
        </h3>
        {estAdmin && (
          <Button variant="primary" onClick={() => setUploadOpen(true)}>
            <Plus size={16} strokeWidth={1.75} className="mr-1.5" />
            Ajouter un document
          </Button>
        )}
      </div>

      {!estAdmin && (
        <div className="flex items-start gap-2 rounded-[var(--radius-sm)] border border-[var(--border)] bg-[var(--surface-2)] px-4 py-3 text-[12.5px] text-[var(--ink-dim)]">
          <KeyRound size={14} strokeWidth={1.75} className="mt-0.5 shrink-0 text-[var(--ink-faint)]" />
          <span>
            Vous consultez la liste en lecture seule. Les documents médicaux et les
            opérations d'écriture sont réservés à l'administrateur.
          </span>
        </div>
      )}

      <div className="flex items-center justify-between gap-3">
        <div className="relative w-[240px]">
          <div className="pointer-events-none absolute left-[9px] top-1/2 -translate-y-1/2 text-[var(--ink-faint)]">
            <Search size={13} strokeWidth={2} />
          </div>
          <Input
            aria-label="Rechercher un document"
            placeholder="Rechercher (nom, entité)…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-[28px]"
          />
        </div>
        <span className="text-[12px] text-[var(--ink-faint)]">
          {visibles.length} document(s)
        </span>
      </div>

      <Card>
        {isError ? (
          <div className="p-5">
            <div className="rounded-[var(--radius-sm)] border border-[var(--danger)]/20 bg-[var(--danger-w)] px-4 py-3 text-sm text-[var(--danger)]">
              {extractErrorMessage(error, 'Impossible de charger les documents.')}
            </div>
          </div>
        ) : isLoading ? (
          <TableSkeleton rows={6} columns={5} />
        ) : visibles.length === 0 ? (
          <div className="p-5">
            <EmptyState
              message={
                search.trim()
                  ? 'Aucun document ne correspond à votre recherche.'
                  : 'Aucun document enregistré.'
              }
            />
          </div>
        ) : (
          <TableContainer className="rounded-none border-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Document</TableHead>
                  <TableHead>Catégorie</TableHead>
                  <TableHead>Entité</TableHead>
                  <TableHead>Taille</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {visibles.map((doc) => (
                  <TableRow key={doc.id}>
                    <TableCell className="max-w-[280px]">
                      <p className="truncate font-medium text-[var(--ink)]">{doc.nom}</p>
                      {doc.nom_fichier_original && doc.nom_fichier_original !== doc.nom && (
                        <p className="truncate text-[11.5px] text-[var(--ink-faint)]">
                          {doc.nom_fichier_original}
                        </p>
                      )}
                      {doc.type_document && (
                        <p className="truncate text-[11.5px] text-[var(--ink-faint)]">
                          {ALL_DOCS_LABELS[doc.type_document] ?? doc.type_document}
                        </p>
                      )}
                    </TableCell>
                    <TableCell>
                      <Badge tone={doc.categorie === 'medical' ? 'danger' : 'neutral'}>
                        {DOC_CATEGORIES[doc.categorie] ?? doc.categorie}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-[var(--ink-dim)]">
                      {doc.entite_label ?? doc.entite_id ?? '—'}
                    </TableCell>
                    <TableCell className="text-[var(--ink-dim)]">
                      {formatFileSize(doc.taille_octets) || '—'}
                    </TableCell>
                    <TableCell className="text-[var(--ink-dim)]">
                      {new Date(doc.created_at).toLocaleDateString('fr-FR')}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-1">
                        <Tooltip content="Télécharger">
                          <Button
                            variant="icon"
                            size="icon"
                            aria-label="Télécharger le document"
                            onClick={() => void telecharger(doc)}
                          >
                            <Download size={14} strokeWidth={1.75} />
                          </Button>
                        </Tooltip>
                        {estAdmin && (
                          <Tooltip content="Supprimer">
                            <Button
                              variant="icon"
                              tone="danger"
                              size="icon"
                              aria-label="Supprimer le document"
                              onClick={() => setDeleting(doc)}
                            >
                              <Trash2 size={14} strokeWidth={1.75} />
                            </Button>
                          </Tooltip>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Card>

      {estAdmin && (
        <AddDocumentDrawer
          open={uploadOpen}
          onClose={() => setUploadOpen(false)}
          title="Ajouter un document"
          labels={DOC_CATEGORIES}
          submitLabel="Importer"
          submitting={uploadMut.isPending}
          onSubmit={soumettre}
        >
          <div className="grid grid-cols-2 gap-3">
            <Select
              label="Type d'entité"
              value={entiteType}
              onChange={(e) => setEntiteType(e.target.value as EntiteDocument)}
              options={ENTITE_OPTIONS}
            />
            <Input
              label="Identifiant (matricule / code)"
              value={entiteId}
              onChange={(e) => setEntiteId(e.target.value)}
              placeholder="ex. ELE-2025-001"
            />
          </div>
        </AddDocumentDrawer>
      )}

      <ConfirmDialog
        open={!!deleting}
        onClose={() => setDeleting(null)}
        onConfirm={() => {
          if (deleting) deleteMut.mutate(deleting.id)
        }}
        isLoading={deleteMut.isPending}
        title="Supprimer ce document ?"
        description={`Supprimer définitivement ${deleting ? `« ${deleting.nom} »` : 'ce document'} ?`}
        confirmLabel="Supprimer"
        variant="danger"
      />
    </div>
  )
}
