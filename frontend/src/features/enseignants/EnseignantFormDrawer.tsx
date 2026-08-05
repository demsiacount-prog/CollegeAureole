import { useState, useEffect } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Drawer } from '@/components/ui/Drawer'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { createEnseignant, updateEnseignant } from './api'
import { extractErrorMessage } from '@/lib/api'
import { toast } from '@/components/ui/toast'
import type { Enseignant, EnseignantCreateInput } from './types'

interface Props {
  open: boolean
  onClose: () => void
  enseignant?: Enseignant | null
}

export default function EnseignantFormDrawer({ open, onClose, enseignant }: Props) {
  const qc = useQueryClient()
  const isEdit = !!enseignant

  const [form, setForm] = useState<EnseignantCreateInput>({
    nom: '',
    prenom: '',
    telephone: '',
    email: '',
    adresse: '',
    specialite: '',
    heures_hebdo_max: null,
  })
  const [error, setError] = useState('')

  useEffect(() => {
    if (open) {
      setForm({
        nom: enseignant?.nom ?? '',
        prenom: enseignant?.prenom ?? '',
        telephone: enseignant?.telephone ?? '',
        email: enseignant?.email ?? '',
        adresse: enseignant?.adresse ?? '',
        specialite: enseignant?.specialite ?? '',
        heures_hebdo_max: enseignant?.heures_hebdo_max ?? null,
      })
      setError('')
    }
  }, [open, enseignant])

  const set = (k: keyof EnseignantCreateInput) =>
    (e: React.ChangeEvent<HTMLInputElement>) =>
      setForm((f) => ({ ...f, [k]: e.target.value }))

  const mutation = useMutation({
    mutationFn: () =>
      isEdit
        ? updateEnseignant(enseignant!.matricule, form)
        : createEnseignant(form),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['enseignants'] })
      qc.invalidateQueries({ queryKey: ['enseignant-dossier'] })
      toast(isEdit ? 'Enseignant modifié.' : 'Enseignant créé.')
      onClose()
    },
    onError: (err) => setError(extractErrorMessage(err)),
  })

  return (
    <Drawer
      open={open}
      onClose={onClose}
      title={isEdit ? "Modifier l'enseignant" : 'Nouvel enseignant'}
    >
      <form
        onSubmit={(e) => { e.preventDefault(); mutation.mutate() }}
        className="flex flex-col h-full"
      >
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <Input label="Prénom" placeholder="ex. Mamadou" value={form.prenom} onChange={set('prenom')} required />
            <Input label="Nom" placeholder="ex. Condé" value={form.nom} onChange={set('nom')} required />
          </div>
          <Input label="Spécialité" placeholder="ex. Mathématiques" value={form.specialite} onChange={set('specialite')} required />
          <Input label="E-mail" type="email" placeholder="ex. mamadou.conde@ecole.ml" value={form.email} onChange={set('email')} required />
          <Input label="Téléphone" value={form.telephone} onChange={set('telephone')} placeholder="+223 XX XX XX XX" />
          <Input label="Adresse" placeholder="ex. Hamdallaye, Bamako" value={form.adresse} onChange={set('adresse')} />
          <Input
            label="Quota horaire max (h/semaine)"
            type="number"
            min={0}
            placeholder="ex. 20"
            value={form.heures_hebdo_max != null ? String(form.heures_hebdo_max) : ''}
            onChange={(e) => setForm((f) => ({ ...f, heures_hebdo_max: e.target.value ? Number(e.target.value) : null }))}
          />
          {error && (
            <p className="rounded-[var(--radius-sm)] border border-[var(--color-danger)]/20 bg-[var(--color-danger)]/10 px-3 py-2 text-sm text-[var(--color-danger)]">
              {error}
            </p>
          )}
        </div>

        <div className="mt-6 flex justify-end gap-2">
          <Button type="button" variant="ghost" onClick={onClose}>Annuler</Button>
          <Button type="submit" variant="primary" isLoading={mutation.isPending}>
            {isEdit ? 'Enregistrer' : 'Créer'}
          </Button>
        </div>
      </form>
    </Drawer>
  )
}
