import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Drawer } from '@/components/ui/Drawer'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { Button } from '@/components/ui/Button'
import { createClasse, updateClasse } from './api'
import { fetchSalles } from '@/features/salles/api'
import { extractErrorMessage } from '@/lib/api'
import { toast } from '@/components/ui/toast'
import { required, minNumber, validateFields, hasErrors, type Errors } from '@/lib/validation'
import type { Classe } from '@/features/shared/types'
import type { ClasseCreateInput } from './api'

const NIVEAUX = [
  '1ère Année', '2ème Année', '3ème Année',
  '4ème Année', '5ème Année', '6ème Année',
  '7ème Année', '8ème Année', '9ème Année',
].map((n) => ({ value: n, label: n }))

interface Props {
  open: boolean
  onClose: () => void
  classe?: Classe | null
}

export function ClasseFormDrawer({ open, onClose, classe }: Props) {
  const qc = useQueryClient()
  const isEdit = !!classe

  const { data: salles = [] } = useQuery({ queryKey: ['salles'], queryFn: fetchSalles })

  const [form, setForm] = useState<ClasseCreateInput>({
    nom: classe?.nom ?? '',
    niveau: classe?.niveau ?? '1ère Année',
    frais_inscription: classe?.frais_inscription ?? 0,
    mensualite: classe?.mensualite ?? 0,
  })
  const [idSalle, setIdSalle] = useState(classe?.id_salle ? String(classe.id_salle) : '')
  const [error, setError] = useState('')
  const [errors, setErrors] = useState<Errors>({})

  // Réinitialise le formulaire à chaque ouverture : sans cela, rouvrir
  // « Nouvelle classe » après une édition affiche les valeurs de celle-ci.
  useEffect(() => {
    if (open) {
      setForm({
        nom: classe?.nom ?? '',
        niveau: classe?.niveau ?? '1ère Année',
        frais_inscription: classe?.frais_inscription ?? 0,
        mensualite: classe?.mensualite ?? 0,
      })
      setIdSalle(classe?.id_salle ? String(classe.id_salle) : '')
      setError('')
      setErrors({})
    }
  }, [open, classe])

  const set = (k: keyof ClasseCreateInput) =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
      setForm((f) => ({ ...f, [k]: e.target.value }))

  const handleSubmit = () => {
    const errs = validateFields({
      nom: required(form.nom, 'Le nom de la classe'),
      niveau: required(form.niveau, 'Le niveau'),
      id_salle: required(idSalle, 'La salle'),
      frais_inscription: minNumber(form.frais_inscription, 0, "Les frais d'inscription"),
      mensualite: minNumber(form.mensualite, 0, 'La mensualité'),
    })
    setErrors(errs)
    if (hasErrors(errs)) return
    mutation.mutate({
      ...form,
      id_salle: idSalle ? Number(idSalle) : null,
    })
  }

  const mutation = useMutation({
    mutationFn: (payload: ClasseCreateInput) =>
      isEdit
        ? updateClasse(classe!.id, payload)
        : createClasse(payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['classes'] })
      toast(isEdit ? 'Classe modifiée.' : 'Classe créée.')
      onClose()
    },
    onError: (err) => setError(extractErrorMessage(err)),
  })

  return (
    <Drawer
      open={open}
      onClose={onClose}
      title={isEdit ? 'Modifier la classe' : 'Nouvelle classe'}
      footer={
        <>
          <Button variant="ghost" onClick={onClose}>Annuler</Button>
          <Button variant="primary" isLoading={mutation.isPending} onClick={handleSubmit}>
            {isEdit ? 'Enregistrer' : 'Créer'}
          </Button>
        </>
      }
    >
      <Input
        label="Nom de la classe"
        value={form.nom}
        onChange={(e) => {
          set('nom')(e)
          if (errors.nom) setErrors((prev) => ({ ...prev, nom: undefined }))
        }}
        placeholder="Ex: A"
        required
        error={errors.nom}
      />
      <Select label="Niveau" value={form.niveau} onChange={set('niveau')} options={NIVEAUX} />
      <Select label="Salle" value={idSalle} onChange={(e) => { setIdSalle(e.target.value); if (errors.id_salle) setErrors((prev) => ({ ...prev, id_salle: undefined })) }} required error={errors.id_salle}>
        <option value="">— Aucune —</option>
        {salles.map((s) => (
          <option key={s.id} value={s.id}>
            {s.nom}{s.capacite != null ? ` (${s.capacite} places)` : ''}
          </option>
        ))}
      </Select>
      <Input
        label="Frais d'inscription (FCFA)"
        type="number"
        placeholder="ex. 25000"
        value={String(form.frais_inscription ?? '')}
        onChange={(e) => {
          setForm((f) => ({ ...f, frais_inscription: Number(e.target.value) }))
          if (errors.frais_inscription) setErrors((prev) => ({ ...prev, frais_inscription: undefined }))
        }}
        error={errors.frais_inscription}
      />
      <Input
        label="Mensualité (FCFA)"
        type="number"
        placeholder="ex. 15000"
        value={String(form.mensualite ?? '')}
        onChange={(e) => {
          setForm((f) => ({ ...f, mensualite: Number(e.target.value) }))
          if (errors.mensualite) setErrors((prev) => ({ ...prev, mensualite: undefined }))
        }}
        error={errors.mensualite}
      />
      {error && (
        <p className="rounded-[var(--radius-sm)] border border-[var(--color-danger)]/20 bg-[var(--color-danger)]/10 px-3 py-2 text-sm text-[var(--color-danger)]">
          {error}
        </p>
      )}
    </Drawer>
  )
}
