import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Drawer } from '@/components/ui/Drawer'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { Button } from '@/components/ui/Button'
import { createClasse, updateClasse } from './api'
import { extractErrorMessage } from '@/lib/api'
import { toast } from '@/components/ui/toast'
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

  const [form, setForm] = useState<ClasseCreateInput>({
    nom: classe?.nom ?? '',
    niveau: classe?.niveau ?? '1ère Année',
    frais_inscription: classe?.frais_inscription ?? 0,
    mensualite: classe?.mensualite ?? 0,
  })
  const [error, setError] = useState('')

  const set = (k: keyof ClasseCreateInput) =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
      setForm((f) => ({ ...f, [k]: e.target.value }))

  const mutation = useMutation({
    mutationFn: () =>
      isEdit
        ? updateClasse(classe!.id, form)
        : createClasse(form),
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
          <Button variant="primary" isLoading={mutation.isPending} onClick={() => mutation.mutate()}>
            {isEdit ? 'Enregistrer' : 'Créer'}
          </Button>
        </>
      }
    >
      <Input label="Nom de la classe" value={form.nom} onChange={set('nom')} placeholder="Ex: A" required />
      <Select label="Niveau" value={form.niveau} onChange={set('niveau')} options={NIVEAUX} />
      <Input label="Frais d'inscription (FCFA)" type="number" placeholder="ex. 25000" value={String(form.frais_inscription ?? '')} onChange={(e) => setForm((f) => ({ ...f, frais_inscription: Number(e.target.value) }))} />
      <Input label="Mensualité (FCFA)" type="number" placeholder="ex. 15000" value={String(form.mensualite ?? '')} onChange={(e) => setForm((f) => ({ ...f, mensualite: Number(e.target.value) }))} />
      {error && (
        <p className="rounded-[var(--radius-sm)] border border-[var(--color-danger)]/20 bg-[var(--color-danger)]/10 px-3 py-2 text-sm text-[var(--color-danger)]">
          {error}
        </p>
      )}
    </Drawer>
  )
}
