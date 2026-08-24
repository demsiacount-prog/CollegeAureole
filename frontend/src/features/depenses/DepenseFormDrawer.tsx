import { useState, useEffect } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Drawer } from '@/components/ui/Drawer'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { Button } from '@/components/ui/Button'
import { extractErrorMessage } from '@/lib/api'
import { toast } from '@/components/ui/toast'
import { createDepense, updateDepense } from './api'
import { required, positiveNumber, validateFields, hasErrors, type Errors } from '@/lib/validation'
import { CATEGORIES, CATEGORIE_LABELS, type CategorieDepense, type Depense } from './types'

interface Props {
  open: boolean
  onClose: () => void
  depense?: Depense | null
}

export default function DepenseFormDrawer({ open, onClose, depense }: Props) {
  const qc = useQueryClient()
  const isEdit = !!depense

  const [libelle, setLibelle] = useState('')
  const [montant, setMontant] = useState('')
  const [categorie, setCategorie] = useState<CategorieDepense>('AUTRE')
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10))
  const [description, setDescription] = useState('')
  const [error, setError] = useState('')
  const [errors, setErrors] = useState<Errors>({})

  useEffect(() => {
    if (open) {
      setLibelle(depense?.libelle ?? '')
      setMontant(depense ? String(depense.montant) : '')
      setCategorie(depense?.categorie ?? 'AUTRE')
      setDate(depense?.date ?? new Date().toISOString().slice(0, 10))
      setDescription(depense?.description ?? '')
      setError('')
      setErrors({})
    }
  }, [open, depense])

  const mutation = useMutation({
    mutationFn: () => {
      const body = {
        libelle,
        montant: Number(montant),
        categorie,
        date,
        description: description || null,
      }
      return isEdit ? updateDepense(depense!.id, body) : createDepense(body)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['depenses'] })
      toast(isEdit ? 'Dépense modifiée.' : 'Dépense créée.')
      onClose()
    },
    onError: (err) => setError(extractErrorMessage(err)),
  })

  const handleSubmit = () => {
    const errs = validateFields({
      libelle: required(libelle, 'Le libellé'),
      montant: positiveNumber(montant, 'Le montant'),
      date: required(date, 'La date'),
    })
    setErrors(errs)
    if (hasErrors(errs)) return
    mutation.mutate()
  }

  return (
    <Drawer open={open} onClose={onClose} title={isEdit ? 'Modifier la dépense' : 'Nouvelle dépense'}>
      <form onSubmit={(e) => { e.preventDefault(); handleSubmit() }} noValidate className="flex flex-col h-full">
        <div className="space-y-4">
          <Input
            label="Libellé"
            placeholder="ex. Achat de fournitures"
            value={libelle}
            onChange={(e) => {
              setLibelle(e.target.value)
              if (errors.libelle) setErrors((prev) => ({ ...prev, libelle: undefined }))
            }}
            required
            error={errors.libelle}
          />
          <Input
            label="Montant (FCFA)"
            type="number"
            min={1}
            step={1}
            placeholder="ex. 5000"
            value={montant}
            onChange={(e) => {
              setMontant(e.target.value)
              if (errors.montant) setErrors((prev) => ({ ...prev, montant: undefined }))
            }}
            required
            error={errors.montant}
          />
          <Select label="Catégorie" value={categorie} onChange={(e) => setCategorie(e.target.value as CategorieDepense)}>
            {CATEGORIES.map((c) => <option key={c} value={c}>{CATEGORIE_LABELS[c]}</option>)}
          </Select>
          <Input
            label="Date"
            type="date"
            value={date}
            onChange={(e) => {
              setDate(e.target.value)
              if (errors.date) setErrors((prev) => ({ ...prev, date: undefined }))
            }}
            max={new Date().toISOString().split('T')[0]}
            required
            error={errors.date}
          />
          <Input label="Description" value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Facultatif" />
          {error && (
            <p className="rounded-[var(--radius-sm)] border border-[var(--color-danger)]/20 bg-[var(--color-danger)]/10 px-3 py-2 text-sm text-[var(--color-danger)]">
              {error}
            </p>
          )}
        </div>

        <div className="mt-6 flex justify-end gap-2">
          <Button type="button" variant="ghost" onClick={onClose}>Annuler</Button>
          <Button type="submit" variant="primary" isLoading={mutation.isPending}>{isEdit ? 'Enregistrer' : 'Créer'}</Button>
        </div>
      </form>
    </Drawer>
  )
}
