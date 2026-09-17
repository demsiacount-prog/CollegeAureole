import { useEffect, useState } from 'react'
import { Button } from '@/components/ui/Button'
import { Drawer } from '@/components/ui/Drawer'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { Textarea } from '@/components/ui/Textarea'
import { UploadZone } from './UploadZone'
import { DOC_CATEGORIES, DOC_CATEGORY_ORDER } from './labels'
import type { DocumentCategorieKey } from './types'

interface UploadDrawerProps {
  open: boolean
  onClose: () => void
  onSubmit: (payload: { fichier: File; nom?: string; categorie: DocumentCategorieKey }) => void
  isLoading?: boolean
  /** Fichier déjà sélectionné (zone de dépôt bas de liste) à pré-remplir. */
  initialFile?: File | null
}

function sansExtension(nom: string): string {
  const idx = nom.lastIndexOf('.')
  return idx > 0 ? nom.slice(0, idx) : nom
}

/** Drawer d'ajout de document (Type K) — nom, catégorie, zone de dépôt. */
export function UploadDrawer({ open, onClose, onSubmit, isLoading, initialFile }: UploadDrawerProps) {
  const [fichier, setFichier] = useState<File | null>(null)
  const [nom, setNom] = useState('')
  const [categorie, setCategorie] = useState<DocumentCategorieKey>('autre')
  const [commentaire, setCommentaire] = useState('')

  useEffect(() => {
    if (open) {
      const fichierInitial = initialFile ?? null
      setFichier(fichierInitial)
      setNom(fichierInitial ? sansExtension(fichierInitial.name) : '')
      setCategorie('autre')
      setCommentaire('')
    }
  }, [open, initialFile])

  function handleSelect(file: File) {
    setFichier(file)
    setNom((n) => (n.trim() ? n : sansExtension(file.name)))
  }

  const valide = !!fichier

  function submit() {
    if (!fichier) return
    const data = { fichier, nom: nom.trim() || undefined, categorie }
    if (commentaire.trim()) {
      // Le commentaire n'est pas persisté par l'API §46 : on l'ignore ici.
    }
    onSubmit(data)
  }

  return (
    <Drawer
      open={open}
      onClose={onClose}
      onSubmit={submit}
      title="Ajouter un document"
      description="Joindre une pièce au dossier courant."
      size="md"
      footer={
        <>
          <Button variant="ghost" onClick={onClose} disabled={isLoading}>
            Annuler
          </Button>
          <Button variant="primary" onClick={submit} disabled={!valide} isLoading={isLoading}>
            Enregistrer
          </Button>
        </>
      }
    >
      <div className="flex flex-col gap-4">
        <Input
          label="Nom du document"
          placeholder="ex : CNI_Aminata_Diallo"
          value={nom}
          onChange={(e) => setNom(e.target.value)}
          maxLength={120}
        />
        <Select
          label="Catégorie"
          value={categorie}
          onChange={(e) => setCategorie(e.target.value as DocumentCategorieKey)}
          options={DOC_CATEGORY_ORDER.map((key) => ({ value: key, label: DOC_CATEGORIES[key] }))}
        />
        {fichier ? (
          <div className="flex items-center gap-2.5 rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--surface-2)] px-3.5 py-2.5">
            <span className="doc-list-icon">
              <span className="text-[11px] font-bold uppercase tracking-wide text-[var(--ink-dim)]">
                {fichier.name.split('.').pop()?.slice(0, 4) ?? 'FILE'}
              </span>
            </span>
            <span className="min-w-0 flex-1">
              <p className="truncate text-[12.5px] font-medium text-[var(--ink)]">{fichier.name}</p>
              <p className="text-[11px] text-[var(--ink-faint)]">
                {(fichier.size / 1024 / 1024).toFixed(2)} Mo · prêt à enregistrer
              </p>
            </span>
            <button
              type="button"
              className="text-[12px] text-[var(--danger)] hover:underline"
              onClick={() => setFichier(null)}
            >
              Retirer
            </button>
          </div>
        ) : (
          <UploadZone compact onSelect={handleSelect} />
        )}
        <Textarea
          label="Commentaire (optionnel)"
          placeholder="Précision utile sur cette pièce…"
          value={commentaire}
          onChange={(e) => setCommentaire(e.target.value)}
          rows={3}
        />
        {!fichier && (
          <p className="text-[11.5px] text-[var(--ink-faint)]">Un fichier est requis pour enregistrer.</p>
        )}
      </div>
    </Drawer>
  )
}