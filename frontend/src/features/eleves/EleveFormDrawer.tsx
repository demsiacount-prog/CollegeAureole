import { useEffect, useState, type FormEvent } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Drawer } from '@/components/ui/Drawer'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { Button } from '@/components/ui/Button'
import { fetchTuteurs } from '@/features/tuteurs/api'
import { fetchClasses } from '@/features/classes/api'
import { extractErrorMessage } from '@/lib/api'
import type { Eleve, EleveCreateInput, EleveUpdateInput } from './types'

interface EleveFormDrawerProps {
  open: boolean
  onClose: () => void
  eleve: Eleve | null // null = création
  onCreate: (payload: EleveCreateInput) => Promise<unknown>
  onUpdate: (matricule: string, payload: EleveUpdateInput) => Promise<unknown>
}

const emptyForm = {
  nom: '',
  prenom: '',
  date_de_naissance: '',
  lieu_de_naissance: '',
  sexe: 'M',
  adresse: '',
  statut: 'actif',
  tuteur_id: '',
  classe_id: '',
}

export function EleveFormDrawer({ open, onClose, eleve, onCreate, onUpdate }: EleveFormDrawerProps) {
  const isEdit = !!eleve
  const [form, setForm] = useState(emptyForm)
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const { data: tuteurs = [] } = useQuery({ queryKey: ['tuteurs'], queryFn: fetchTuteurs, enabled: open })
  const { data: classes = [] } = useQuery({ queryKey: ['classes'], queryFn: fetchClasses, enabled: open })

  useEffect(() => {
    if (!open) return
    if (eleve) {
      setForm({
        nom: eleve.nom,
        prenom: eleve.prenom,
        date_de_naissance: eleve.date_de_naissance,
        lieu_de_naissance: eleve.lieu_de_naissance,
        sexe: eleve.sexe,
        adresse: eleve.adresse ?? '',
        statut: eleve.statut,
        tuteur_id: String(eleve.tuteur.id),
        classe_id: eleve.classe ? String(eleve.classe.id) : '',
      })
    } else {
      setForm(emptyForm)
    }
    setError(null)
  }, [open, eleve])

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setIsSubmitting(true)
    try {
      if (isEdit && eleve) {
        await onUpdate(eleve.matricule, {
          nom: form.nom,
          prenom: form.prenom,
          lieu_de_naissance: form.lieu_de_naissance,
          adresse: form.adresse || null,
          statut: form.statut,
          classe_id: form.classe_id ? Number(form.classe_id) : null,
        })
      } else {
        await onCreate({
          nom: form.nom,
          prenom: form.prenom,
          date_de_naissance: form.date_de_naissance,
          lieu_de_naissance: form.lieu_de_naissance,
          sexe: form.sexe,
          adresse: form.adresse || null,
          statut: form.statut,
          tuteur_id: Number(form.tuteur_id),
          classe_id: form.classe_id ? Number(form.classe_id) : null,
        })
      }
      onClose()
    } catch (err) {
      setError(extractErrorMessage(err, "L'enregistrement a échoué."))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <Drawer
      open={open}
      onClose={onClose}
      title={isEdit ? `Modifier ${eleve?.prenom} ${eleve?.nom}` : 'Nouvel élève'}
      description={isEdit ? `Matricule ${eleve?.matricule}` : 'Créer un dossier élève et l’associer à un tuteur.'}
    >
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div className="grid grid-cols-2 gap-3">
          <Input label="Prénom" value={form.prenom} onChange={(e) => setForm({ ...form, prenom: e.target.value })} required />
          <Input label="Nom" value={form.nom} onChange={(e) => setForm({ ...form, nom: e.target.value })} required />
        </div>

        {!isEdit && (
          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Date de naissance"
              type="date"
              value={form.date_de_naissance}
              onChange={(e) => setForm({ ...form, date_de_naissance: e.target.value })}
              required
            />
            <Select label="Sexe" value={form.sexe} onChange={(e) => setForm({ ...form, sexe: e.target.value })}>
              <option value="M">Masculin</option>
              <option value="F">Féminin</option>
            </Select>
          </div>
        )}

        <Input
          label="Lieu de naissance"
          value={form.lieu_de_naissance}
          onChange={(e) => setForm({ ...form, lieu_de_naissance: e.target.value })}
          required
        />
        <Input label="Adresse" value={form.adresse} onChange={(e) => setForm({ ...form, adresse: e.target.value })} />

        <div className="grid grid-cols-2 gap-3">
          <Select label="Classe" value={form.classe_id} onChange={(e) => setForm({ ...form, classe_id: e.target.value })}>
            <option value="">Non affecté</option>
            {classes.map((c) => (
              <option key={c.id} value={c.id}>
                {c.niveau} — {c.nom}
              </option>
            ))}
          </Select>
          <Select label="Statut" value={form.statut} onChange={(e) => setForm({ ...form, statut: e.target.value })}>
            <option value="actif">Actif</option>
            <option value="inactif">Inactif</option>
          </Select>
        </div>

        {!isEdit && (
          <Select
            label="Tuteur"
            value={form.tuteur_id}
            onChange={(e) => setForm({ ...form, tuteur_id: e.target.value })}
            required
          >
            <option value="" disabled>
              Sélectionner un tuteur
            </option>
            {tuteurs.map((t) => (
              <option key={t.id} value={t.id}>
                {t.prenom} {t.nom} — {t.telephone}
              </option>
            ))}
          </Select>
        )}

        {error && (
          <p role="alert" className="rounded-[var(--radius-sm)] border border-[var(--color-danger)]/30 bg-[var(--color-danger-wash)] px-3 py-2 text-sm text-[var(--color-danger)]">
            {error}
          </p>
        )}

        <div className="mt-2 flex justify-end gap-2">
          <Button type="button" variant="ghost" onClick={onClose}>
            Annuler
          </Button>
          <Button type="submit" variant="primary" isLoading={isSubmitting}>
            {isEdit ? 'Enregistrer' : 'Créer l’élève'}
          </Button>
        </div>
      </form>
    </Drawer>
  )
}
