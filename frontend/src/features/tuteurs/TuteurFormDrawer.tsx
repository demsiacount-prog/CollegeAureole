import { useEffect, useState, type FormEvent } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Drawer } from '@/components/ui/Drawer'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { createTuteur, updateTuteur } from './api'
import { extractErrorMessage } from '@/lib/api'
import { toast } from '@/components/ui/toast'
import { required, email, phone, validateFields, hasErrors, type Errors } from '@/lib/validation'
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
  const [errors, setErrors] = useState<Errors>({})

  useEffect(() => {
    if (!open) return
    if (tuteur) {
      setForm({
        nom: tuteur.nom,
        prenom: tuteur.prenom,
        telephone: tuteur.telephone ?? '',
        email: tuteur.email ?? '',
        adresse: tuteur.adresse ?? '',
        profession: tuteur.profession ?? '',
      })
    } else {
      setForm(emptyForm)
    }
    setError(null)
    setErrors({})
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
    const errs = validateFields({
      prenom: required(form.prenom, 'Le prénom'),
      nom: required(form.nom, 'Le nom'),
      telephone: required(form.telephone, 'Le téléphone') ?? phone(form.telephone),
      email: required(form.email, "L'e-mail") ?? email(form.email),
      profession: required(form.profession, 'La profession'),
      adresse: required(form.adresse, "L'adresse"),
    })
    setErrors(errs)
    if (hasErrors(errs)) return
    mutation.mutate()
  }

  return (
    <Drawer
      open={open}
      onClose={onClose}
      title={isEdit ? 'Modifier le tuteur' : 'Nouveau tuteur'}
      description={isEdit ? `${tuteur?.prenom} ${tuteur?.nom}` : "Ajouter un tuteur et l'associer à un élève."}
    >
      <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-4">
        <div className="grid grid-cols-2 gap-3">
          <Input
            label="Prénom"
            placeholder="ex. Amadou"
            value={form.prenom}
            onChange={(e) => {
              set('prenom')(e)
              if (errors.prenom) setErrors((prev) => ({ ...prev, prenom: undefined }))
            }}
            required
            error={errors.prenom}
          />
          <Input
            label="Nom"
            placeholder="ex. Touré"
            value={form.nom}
            onChange={(e) => {
              set('nom')(e)
              if (errors.nom) setErrors((prev) => ({ ...prev, nom: undefined }))
            }}
            required
            error={errors.nom}
          />
        </div>
        <Input
          label="Téléphone"
          value={form.telephone}
          onChange={(e) => {
            set('telephone')(e)
            if (errors.telephone) setErrors((prev) => ({ ...prev, telephone: undefined }))
          }}
          placeholder="+223 XX XX XX XX"
          required
          error={errors.telephone}
        />
        <Input
          label="E-mail"
          type="email"
          value={form.email}
          onChange={(e) => {
            set('email')(e)
            if (errors.email) setErrors((prev) => ({ ...prev, email: undefined }))
          }}
          placeholder="ex. amadou@email.com"
          error={errors.email}
        />
        <Input label="Profession" value={form.profession} onChange={(e) => {
          set('profession')(e)
          if (errors.profession) setErrors((prev) => ({ ...prev, profession: undefined }))
        }} placeholder="ex. Enseignant" required error={errors.profession} />
        <Input label="Adresse" value={form.adresse} onChange={(e) => {
          set('adresse')(e)
          if (errors.adresse) setErrors((prev) => ({ ...prev, adresse: undefined }))
        }} placeholder="ex. Badalabougou, Bamako" required error={errors.adresse} />

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
