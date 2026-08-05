import { useEffect, useState, type FormEvent } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Drawer } from '@/components/ui/Drawer'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { createTuteur, updateTuteur } from './api'
import { extractErrorMessage } from '@/lib/api'
import { toast } from '@/components/ui/toast'
import type { Tuteur } from '@/features/shared/types'
import type { TuteurCreateInput } from './api'

interface Props {
  open: boolean
  onClose: () => void
  tuteur?: Tuteur
  onCreated?: (tuteur: Tuteur) => void
}

const emptyForm: TuteurCreateInput = {
  nom: '',
  prenom: '',
  telephone: '',
  email: '',
  adresse: '',
  profession: '',
}

export function TuteurFormDrawer({ open, onClose, tuteur, onCreated }: Props) {
  const qc = useQueryClient()
  const isEdit = !!tuteur

  const [form, setForm] = useState<TuteurCreateInput>(emptyForm)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!open) return
    if (tuteur) {
      setForm({
        nom: tuteur.nom,
        prenom: tuteur.prenom,
        telephone: tuteur.telephone,
        email: tuteur.email,
        adresse: tuteur.adresse,
        profession: tuteur.profession,
      })
    } else {
      setForm(emptyForm)
    }
    setError(null)
  }, [open, tuteur])

  const set = (k: keyof TuteurCreateInput) =>
    (e: React.ChangeEvent<HTMLInputElement>) =>
      setForm((f) => ({ ...f, [k]: e.target.value }))

  const mutation = useMutation({
    mutationFn: () =>
      isEdit
        ? updateTuteur(tuteur!.id, form)
        : createTuteur(form),
    onSuccess: (created) => {
      qc.invalidateQueries({ queryKey: ['tuteurs'] })
      toast(isEdit ? 'Tuteur modifié.' : 'Tuteur créé.')
      if (!isEdit && onCreated) onCreated(created)
      onClose()
    },
    onError: (err) => setError(extractErrorMessage(err)),
  })

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    mutation.mutate()
  }

  return (
    <Drawer
      open={open}
      onClose={onClose}
      title={isEdit ? 'Modifier le tuteur' : 'Nouveau tuteur'}
      description={isEdit ? `${tuteur?.prenom} ${tuteur?.nom}` : "Ajouter un tuteur et l'associer à un élève."}
    >
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div className="grid grid-cols-2 gap-3">
          <Input label="Prénom" placeholder="ex. Amadou" value={form.prenom} onChange={set('prenom')} required />
          <Input label="Nom" placeholder="ex. Touré" value={form.nom} onChange={set('nom')} required />
        </div>
        <Input label="Téléphone" value={form.telephone} onChange={set('telephone')} placeholder="+223 XX XX XX XX" required />
        <Input label="E-mail" type="email" value={form.email} onChange={set('email')} placeholder="ex. amadou@email.com" />
        <Input label="Profession" value={form.profession} onChange={set('profession')} placeholder="ex. Enseignant" />
        <Input label="Adresse" value={form.adresse} onChange={set('adresse')} placeholder="ex. Badalabougou, Bamako" />

        {error && (
          <p role="alert" className="rounded-[var(--radius-sm)] border border-[var(--color-danger)]/30 bg-[var(--color-danger-wash)] px-3 py-2 text-sm text-[var(--color-danger)]">
            {error}
          </p>
        )}

        <div className="mt-2 flex justify-end gap-2">
          <Button type="button" variant="ghost" onClick={onClose}>
            Annuler
          </Button>
          <Button type="submit" variant="primary" isLoading={mutation.isPending}>
            {isEdit ? 'Enregistrer' : 'Créer'}
          </Button>
        </div>
      </form>
    </Drawer>
  )
}
