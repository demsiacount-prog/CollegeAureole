import { useState, useEffect } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Drawer } from '@/components/ui/Drawer'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
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
    genre: '',
    nina: '',
    date_naissance: '',
    lieu_de_naissance: '',
    nationalite: '',
    situation_matrimoniale: '',
    categorie: '',
    echelon: '',
    fonction: '',
    sf_nombre_enfants: '',
    date_contrat: '',
    date_titularisation: '',
    date_dernier_avancement: '',
    classe_tenue: '',
    dernier_poste: '',
    date_arrivee_cap: '',
    diplome: '',
    observations: '',
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
        genre: enseignant?.genre ?? '',
        nina: enseignant?.nina ?? '',
        date_naissance: enseignant?.date_naissance ?? '',
        lieu_de_naissance: enseignant?.lieu_de_naissance ?? '',
        nationalite: enseignant?.nationalite ?? '',
        situation_matrimoniale: enseignant?.situation_matrimoniale ?? '',
        categorie: enseignant?.categorie ?? '',
        echelon: enseignant?.echelon ?? '',
        fonction: enseignant?.fonction ?? '',
        sf_nombre_enfants: enseignant?.sf_nombre_enfants ?? '',
        date_contrat: enseignant?.date_contrat ?? '',
        date_titularisation: enseignant?.date_titularisation ?? '',
        date_dernier_avancement: enseignant?.date_dernier_avancement ?? '',
        classe_tenue: enseignant?.classe_tenue ?? '',
        dernier_poste: enseignant?.dernier_poste ?? '',
        date_arrivee_cap: enseignant?.date_arrivee_cap ?? '',
        diplome: enseignant?.diplome ?? '',
        observations: enseignant?.observations ?? '',
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
    mutationFn: () => {
      const corps: EnseignantCreateInput = {
        ...form,
        date_naissance: form.date_naissance || undefined,
        date_contrat: form.date_contrat || undefined,
        date_titularisation: form.date_titularisation || undefined,
        date_dernier_avancement: form.date_dernier_avancement || undefined,
        date_arrivee_cap: form.date_arrivee_cap || undefined,
      }
      return isEdit ? updateEnseignant(enseignant!.matricule, corps) : createEnseignant(corps)
    },
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

          <div className="grid grid-cols-2 gap-3 rounded-[var(--radius-sm)] border border-[var(--color-border)] bg-[var(--color-surface-2)] p-3">
            <div className="col-span-2 text-[10px] font-semibold uppercase tracking-wide text-[var(--color-ink-dim)]">
              Renseignements administratifs
            </div>
            <Select
              label="Genre"
              value={form.genre ?? ''}
              onChange={(e) => {
                setForm((f) => ({ ...f, genre: e.target.value }))
              }}
              options={[
                { value: '', label: '—' },
                { value: 'M', label: 'Masculin' },
                { value: 'F', label: 'Féminin' },
              ]}
            />
            <Input
              label="NINA"
              value={form.nina ?? ''}
              onChange={(e) => setForm((f) => ({ ...f, nina: e.target.value }))}
            />
            <Input
              label="Date de naissance"
              type="date"
              value={form.date_naissance ?? ''}
              onChange={(e) => setForm((f) => ({ ...f, date_naissance: e.target.value }))}
            />
            <Input
              label="Lieu de naissance"
              placeholder="ex. Bamako"
              value={form.lieu_de_naissance ?? ''}
              onChange={(e) => setForm((f) => ({ ...f, lieu_de_naissance: e.target.value }))}
            />
            <Input
              label="Nationalité"
              placeholder="ex. Malienne"
              value={form.nationalite ?? ''}
              onChange={(e) => setForm((f) => ({ ...f, nationalite: e.target.value }))}
            />
            <Select
              label="Situation matrimoniale"
              value={form.situation_matrimoniale ?? ''}
              onChange={(e) => setForm((f) => ({ ...f, situation_matrimoniale: e.target.value }))}
              options={[
                { value: '', label: '—' },
                { value: 'Célibataire', label: 'Célibataire' },
                { value: 'Marié(e)', label: 'Marié(e)' },
                { value: 'Divorcé(e)', label: 'Divorcé(e)' },
                { value: 'Veuf(ve)', label: 'Veuf(ve)' },
              ]}
            />
            <Input
              label="Catégorie"
              placeholder="ex. Titulaire / Contractuel"
              value={form.categorie ?? ''}
              onChange={(e) => setForm((f) => ({ ...f, categorie: e.target.value }))}
            />
            <Input
              label="Échelon"
              value={form.echelon ?? ''}
              onChange={(e) => setForm((f) => ({ ...f, echelon: e.target.value }))}
            />
            <Input
              label="Fonction"
              placeholder="ex. Directeur / Enseignant"
              value={form.fonction ?? ''}
              onChange={(e) => setForm((f) => ({ ...f, fonction: e.target.value }))}
            />
            <Input
              label="Nbre d’enfants (SF)"
              value={form.sf_nombre_enfants ?? ''}
              onChange={(e) => setForm((f) => ({ ...f, sf_nombre_enfants: e.target.value }))}
            />
            <Input
              label="Date de contrat"
              type="date"
              value={form.date_contrat ?? ''}
              onChange={(e) => setForm((f) => ({ ...f, date_contrat: e.target.value }))}
            />
            <Input
              label="Date de titularisation"
              type="date"
              value={form.date_titularisation ?? ''}
              onChange={(e) => setForm((f) => ({ ...f, date_titularisation: e.target.value }))}
            />
            <Input
              label="Date du dernier avancement"
              type="date"
              value={form.date_dernier_avancement ?? ''}
              onChange={(e) => setForm((f) => ({ ...f, date_dernier_avancement: e.target.value }))}
            />
            <Input
              label="Classe tenue"
              value={form.classe_tenue ?? ''}
              onChange={(e) => setForm((f) => ({ ...f, classe_tenue: e.target.value }))}
            />
            <Input
              label="Dernier poste occupé"
              value={form.dernier_poste ?? ''}
              onChange={(e) => setForm((f) => ({ ...f, dernier_poste: e.target.value }))}
            />
            <Input
              label="Date d’arrivée au CAP"
              type="date"
              value={form.date_arrivee_cap ?? ''}
              onChange={(e) => setForm((f) => ({ ...f, date_arrivee_cap: e.target.value }))}
            />
            <Input
              label="Diplôme"
              value={form.diplome ?? ''}
              onChange={(e) => setForm((f) => ({ ...f, diplome: e.target.value }))}
            />
            <div className="col-span-2">
              <Input
                label="Observations"
                value={form.observations ?? ''}
                onChange={(e) => setForm((f) => ({ ...f, observations: e.target.value }))}
              />
            </div>
          </div>

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
