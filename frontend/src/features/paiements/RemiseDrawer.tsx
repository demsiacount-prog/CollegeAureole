import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Trash2 } from 'lucide-react'
import { Drawer } from '@/components/ui/Drawer'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { extractErrorMessage } from '@/lib/api'
import { formatMontant, formatDate } from '@/lib/format'
import { toast } from '@/components/ui/toast'
import { fetchRemises, createRemise, deleteRemise } from './api'
import { required, positiveNumber, validateFields, hasErrors, type Errors } from '@/lib/validation'
import type { Remise, Echeance } from './types'

export default function RemiseDrawer({ open, onClose, echeance }: {
  open: boolean
  onClose: () => void
  echeance: Echeance | null
}) {
  const qc = useQueryClient()

  const [montant, setMontant] = useState('')
  const [motif, setMotif] = useState('')
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10))
  const [errors, setErrors] = useState<Errors>({})
  const [error, setError] = useState('')
  const [deleting, setDeleting] = useState<Remise | null>(null)

  const { data: remises = [] } = useQuery({
    queryKey: ['remises', echeance?.id],
    queryFn: () => fetchRemises(echeance!.id),
    enabled: open && !!echeance,
  })

  const totalRemises = remises.reduce((s, r) => s + r.montant, 0)
  const resteApresRemises = echeance ? echeance.montant_du - echeance.montant_paye - totalRemises : 0

  const createMut = useMutation({
    mutationFn: () => createRemise(echeance!.id, {
      montant: Number(montant),
      motif: motif || null,
      date,
    }),
    onSuccess: () => {
      toast('Remise appliquée.')
      qc.invalidateQueries({ queryKey: ['remises'] })
      qc.invalidateQueries({ queryKey: ['echeances'] })
      setMontant('')
      setMotif('')
      setDate(new Date().toISOString().slice(0, 10))
      setErrors({})
    },
    onError: (err) => setError(extractErrorMessage(err)),
  })

  const deleteMut = useMutation({
    mutationFn: deleteRemise,
    onSuccess: () => {
      toast('Remise supprimée.')
      qc.invalidateQueries({ queryKey: ['remises'] })
      qc.invalidateQueries({ queryKey: ['echeances'] })
      setDeleting(null)
    },
    onError: (err) => toast(extractErrorMessage(err), 'error'),
  })

  const handleSubmit = () => {
    const errs = validateFields({
      montant: positiveNumber(montant, 'Le montant'),
      date: required(date, 'La date'),
    })
    setErrors(errs)
    if (hasErrors(errs)) return
    if (Number(montant) > resteApresRemises) {
      setErrors({ montant: `Le montant ne peut pas dépasser ${formatMontant(resteApresRemises)}` })
      return
    }
    createMut.mutate()
  }

  if (!echeance) return null

  return (
    <>
      <Drawer open={open} onClose={onClose} title="Remises">
        <div className="flex flex-col h-full">
          <div className="space-y-4">
            <div className="rounded-[var(--radius-sm)] border border-[var(--color-border-soft)] bg-[var(--color-surface-2)] p-3">
              <p className="text-sm font-medium text-[var(--color-ink)]">
                {echeance.type_echeance === 'INSCRIPTION' ? 'Inscription' : echeance.mois}
              </p>
              <div className="mt-2 grid grid-cols-3 gap-2 text-sm">
                <div>
                  <p className="text-xs text-[var(--color-ink-faint)]">Montant dû</p>
                  <p className="font-medium text-[var(--color-ink)]">{formatMontant(echeance.montant_du)}</p>
                </div>
                <div>
                  <p className="text-xs text-[var(--color-ink-faint)]">Payé</p>
                  <p className="font-medium text-[var(--color-ink)]">{formatMontant(echeance.montant_paye)}</p>
                </div>
                <div>
                  <p className="text-xs text-[var(--color-ink-faint)]">Reste</p>
                  <p className="font-medium text-[var(--color-ink)]">{formatMontant(echeance.reste_a_payer)}</p>
                </div>
              </div>
              {totalRemises > 0 && (
                <div className="mt-2 border-t border-[var(--color-border-soft)] pt-2">
                  <p className="text-xs text-[var(--color-ink-faint)]">Total remises</p>
                  <p className="font-medium text-[var(--color-danger)]">-{formatMontant(totalRemises)}</p>
                </div>
              )}
            </div>

            {remises.length > 0 && (
              <div>
                <p className="text-sm font-medium text-[var(--color-ink-dim)]">Remises appliquées</p>
                <ul className="mt-2 space-y-2">
                  {remises.map((r) => (
                    <li key={r.id} className="flex items-start justify-between rounded-[var(--radius-sm)] border border-[var(--color-border-soft)] bg-[var(--color-surface-2)] p-2">
                      <div>
                        <p className="text-sm font-medium text-[var(--color-danger)]">-{formatMontant(r.montant)}</p>
                        {r.motif && <p className="text-xs text-[var(--color-ink-faint)]">{r.motif}</p>}
                        <p className="text-xs text-[var(--color-ink-faint)]">{formatDate(r.date)}</p>
                      </div>
                      <Button
                        variant="icon"
                        tone="danger"
                        size="icon"
                        onClick={() => setDeleting(r)}
                        aria-label="Supprimer cette remise"
                      >
                        <Trash2 strokeWidth={1.75} className="size-3" />
                      </Button>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <div className="border-t border-[var(--color-border-soft)] pt-4">
              <p className="text-sm font-medium text-[var(--color-ink-dim)]">Nouvelle remise</p>
              <div className="mt-2 space-y-3">
                <Input
                  label="Montant (FCFA)"
                  type="number"
                  min={1}
                  step={0.01}
                  placeholder="ex. 5000"
                  value={montant}
                  onChange={(e) => {
                    setMontant(e.target.value)
                    if (errors.montant) setErrors((prev) => ({ ...prev, montant: undefined }))
                  }}
                  required
                  error={errors.montant}
                />
                <Input
                  label="Motif"
                  value={motif}
                  onChange={(e) => setMotif(e.target.value)}
                  placeholder="Facultatif"
                />
                <Input
                  label="Date"
                  type="date"
                  max={new Date().toISOString().split('T')[0]}
                  value={date}
                  onChange={(e) => {
                    setDate(e.target.value)
                    if (errors.date) setErrors((prev) => ({ ...prev, date: undefined }))
                  }}
                  required
                  error={errors.date}
                />
                {error && (
                  <p className="rounded-[var(--radius-sm)] border border-[var(--color-danger)]/20 bg-[var(--color-danger)]/10 px-3 py-2 text-sm text-[var(--color-danger)]">
                    {error}
                  </p>
                )}
                <Button variant="primary" onClick={handleSubmit} isLoading={createMut.isPending}>
                  Appliquer la remise
                </Button>
              </div>
            </div>
          </div>
        </div>
      </Drawer>

      <ConfirmDialog
        open={!!deleting}
        onClose={() => setDeleting(null)}
        onConfirm={() => { if (deleting) deleteMut.mutate(deleting.id) }}
        title="Supprimer cette remise ?"
        description={`Êtes-vous sûr de vouloir supprimer la remise de ${deleting ? formatMontant(deleting.montant) : ''} ?`}
        confirmLabel="Supprimer"
        variant="danger"
      />
    </>
  )
}
