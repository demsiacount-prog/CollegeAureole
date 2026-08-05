import { useState, useEffect } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Drawer } from '@/components/ui/Drawer'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { SearchableSelect } from '@/components/ui/SearchableSelect'
import { Button } from '@/components/ui/Button'
import { Spinner } from '@/components/ui/Spinner'
import { extractErrorMessage } from '@/lib/api'
import { formatMontant } from '@/lib/format'
import { toast } from '@/components/ui/toast'
import { createPaiement, fetchEcheances } from './api'
import { fetchInscriptions } from '@/features/inscriptions/api'

const MODES = ['ESPECES', 'VIREMENT', 'CHEQUE', 'MOBILE_MONEY']

export default function PaiementFormDrawer({ open, onClose }: { open: boolean; onClose: () => void }) {
  const qc = useQueryClient()

  const [idInscription, setIdInscription] = useState<number | ''>('')
  const [montant, setMontant] = useState('')
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10))
  const [mode, setMode] = useState('')
  const [numeroRecu, setNumeroRecu] = useState('')
  const [observation, setObservation] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    if (open) {
      setIdInscription('')
      setMontant('')
      setDate(new Date().toISOString().slice(0, 10))
      setMode('')
      setNumeroRecu('')
      setObservation('')
      setError('')
    }
  }, [open])

  const { data: inscriptions = [], isLoading: loadingInscriptions } = useQuery({
    queryKey: ['inscriptions'],
    queryFn: () => fetchInscriptions(),
    enabled: open,
  })

  const inscriptionId = idInscription !== '' ? Number(idInscription) : null

  const { data: echeances = [], isLoading: loadingEcheances } = useQuery({
    queryKey: ['echeances', inscriptionId],
    queryFn: () => fetchEcheances(inscriptionId!),
    enabled: open && inscriptionId !== null,
  })

  const echeancesImpayees = echeances.filter((e) => e.statut !== 'SOLDE')
  const resteGlobal = echeancesImpayees.reduce((s, e) => s + e.reste_a_payer, 0)

  const mutation = useMutation({
    mutationFn: () => createPaiement({
      id_inscription: Number(idInscription),
      montant: Number(montant),
      date,
      mode: mode || null,
      numero_recu: numeroRecu || null,
      observation: observation || null,
    }),
    onSuccess: (result) => {
      qc.invalidateQueries({ queryKey: ['paiements'] })
      qc.invalidateQueries({ queryKey: ['echeances'] })
      toast(`Paiement enregistré — ${result.nb_paiements_crees} tranches, reste ${formatMontant(result.reste_global)}.`)
      onClose()
    },
    onError: (err) => setError(extractErrorMessage(err)),
  })

  return (
    <Drawer open={open} onClose={onClose} title="Enregistrer un paiement">
      <form onSubmit={(e) => { e.preventDefault(); mutation.mutate() }} className="flex flex-col h-full">
        <div className="space-y-4">
          {loadingInscriptions ? (
            <div className="flex justify-center py-4"><Spinner /></div>
          ) : (
            <SearchableSelect
              label="Élève (inscription)"
              value={idInscription !== '' ? String(idInscription) : ''}
              onChange={(v) => setIdInscription(v ? Number(v) : '')}
              options={inscriptions.map((i) => ({
                value: String(i.id),
                label: `${i.eleve_nom ?? ''} ${i.eleve_prenom ?? ''}`.trim(),
                sublabel: i.matricule_eleve,
              }))}
              placeholder="Rechercher un élève…"
              emptyMessage="Aucun élève trouvé"
            />
          )}

          {inscriptionId && (
            <div className="rounded-[var(--radius-sm)] border border-[var(--color-border-soft)] bg-[var(--color-surface-2)] p-3">
              <p className="text-xs font-medium text-[var(--color-ink-dim)]">Échéances impayées</p>
              {loadingEcheances ? (
                <div className="mt-2 flex justify-center"><Spinner /></div>
              ) : echeancesImpayees.length === 0 ? (
                <p className="mt-1 text-sm text-[var(--color-ink-faint)]">Toutes les échéances sont soldées.</p>
              ) : (
                <ul className="mt-2 space-y-1">
                  {echeancesImpayees.map((ech) => (
                    <li key={ech.id} className="flex items-center justify-between text-sm">
                      <span className="text-[var(--color-ink)]">
                        {ech.type_echeance === 'INSCRIPTION' ? 'Inscription' : ech.mois}
                      </span>
                      <span className="font-medium text-[var(--color-ink)]">{formatMontant(ech.reste_a_payer)}</span>
                    </li>
                  ))}
                </ul>
              )}
              {resteGlobal > 0 && (
                <p className="mt-2 border-t border-[var(--color-border-soft)] pt-2 text-sm font-medium text-[var(--color-ink)]">
                  Reste total : {formatMontant(resteGlobal)}
                </p>
              )}
            </div>
          )}

          <Input
            label="Montant (FCFA)"
            type="number"
            min={1}
            step={0.01}
            placeholder="ex. 25000"
            value={montant}
            onChange={(e) => setMontant(e.target.value)}
            required
          />

          <Input
            label="Date du paiement"
            type="date"
            max={new Date().toISOString().split('T')[0]}
            value={date}
            onChange={(e) => setDate(e.target.value)}
            required
          />

          <Select label="Mode de paiement" value={mode} onChange={(e) => setMode(e.target.value)}>
            <option value="">— Non spécifié —</option>
            {MODES.map((m) => <option key={m} value={m}>{m}</option>)}
          </Select>

          <Input
            label="N° reçu"
            value={numeroRecu}
            onChange={(e) => setNumeroRecu(e.target.value)}
            placeholder="ex. REC-2026-001"
          />

          <Input
            label="Observation"
            value={observation}
            onChange={(e) => setObservation(e.target.value)}
            placeholder="Facultatif"
          />

          {error && (
            <p className="rounded-[var(--radius-sm)] border border-[var(--color-danger)]/20 bg-[var(--color-danger)]/10 px-3 py-2 text-sm text-[var(--color-danger)]">
              {error}
            </p>
          )}
        </div>

        <div className="mt-6 flex justify-end gap-2">
          <Button type="button" variant="ghost" onClick={onClose}>Annuler</Button>
          <Button type="submit" variant="primary" isLoading={mutation.isPending}>Enregistrer</Button>
        </div>
      </form>
    </Drawer>
  )
}
