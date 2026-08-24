import { useState, useEffect } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Drawer } from '@/components/ui/Drawer'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { createEnseignant, updateEnseignant } from './api'
import { extractErrorMessage } from '@/lib/api'
import { toast } from '@/components/ui/toast'
import { required, email, phone, validateFields, hasErrors, type Errors } from '@/lib/validation'
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
  })
  const [error, setError] = useState('')
  const [errors, setErrors] = useState<Errors>({})

  useEffect(() => {
    if (open) {
      setForm({
        nom: enseignant?.nom ?? '',
        prenom: enseignant?.prenom ?? '',
        telephone: enseignant?.telephone ?? '',
        email: enseignant?.email ?? '',
        adresse: enseignant?.adresse ?? '',
        specialite: enseignant?.specialite ?? '',
      })
      setError('')
      setErrors({})
    }
  }, [open, enseignant])

  const set = (k: keyof EnseignantCreateInput) =>
    (e: React.ChangeEvent<HTMLInputElement>) =>
      setForm((f) => ({ ...f, [k]: e.target.value }))

  const handleSubmit = () => {
    const errs = validateFields({
      prenom: required(form.prenom, 'Le prénom'),
      nom: required(form.nom, 'Le nom'),
      specialite: required(form.specialite, 'La spécialité'),
      email: required(form.email, "L'e-mail") ?? email(form.email),
      telephone: required(form.telephone, 'Le téléphone') ?? phone(form.telephone),
      adresse: required(form.adresse, "L'adresse"),
    })
    setErrors(errs)
    if (hasErrors(errs)) return
    mutation.mutate()
  }

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
        onSubmit={(e) => { e.preventDefault(); handleSubmit() }}
        noValidate
        className="flex flex-col h-full"
      >
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Prénom"
              placeholder="ex. Mamadou"
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
              placeholder="ex. Condé"
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
            label="Spécialité"
            placeholder="ex. Mathématiques"
            value={form.specialite}
            onChange={(e) => {
              set('specialite')(e)
              if (errors.specialite) setErrors((prev) => ({ ...prev, specialite: undefined }))
            }}
            required
            error={errors.specialite}
          />
          <Input
            label="E-mail"
            type="email"
            placeholder="ex. mamadou.conde@ecole.ml"
            value={form.email}
            onChange={(e) => {
              set('email')(e)
              if (errors.email) setErrors((prev) => ({ ...prev, email: undefined }))
            }}
            required
            error={errors.email}
          />
          <Input
            label="Téléphone"
            value={form.telephone}
            onChange={(e) => {
              set('telephone')(e)
              if (errors.telephone) setErrors((prev) => ({ ...prev, telephone: undefined }))
            }}
            placeholder="+223 XX XX XX XX"
            error={errors.telephone}
          />
          <Input label="Adresse" placeholder="ex. Hamdallaye, Bamako" value={form.adresse} onChange={(e) => {
            set('adresse')(e)
            if (errors.adresse) setErrors((prev) => ({ ...prev, adresse: undefined }))
          }} error={errors.adresse} />
          
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
