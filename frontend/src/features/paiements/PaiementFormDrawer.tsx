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
import { createPaiement, updatePaiement, fetchEcheances, createPaiementGroupe } from './api'
import { fetchInscriptions } from '@/features/inscriptions/api'
import { fetchTuteurs } from '@/features/tuteurs/api'
import { required, positiveNumber, validateFields, hasErrors, type Errors } from '@/lib/validation'
import type { Paiement, PaiementResult, PaiementGroupeResult, Echeance, RemiseParEcheance } from './types'
import RemiseDrawer from './RemiseDrawer'

const MODES = ['ESPECES', 'VIREMENT', 'CHEQUE', 'MOBILE_MONEY']

export default function PaiementFormDrawer({ open, onClose, paiement, modeGroupe = false }: {
  open: boolean
  onClose: () => void
  paiement?: Paiement | null
  modeGroupe?: boolean
}) {
  const qc = useQueryClient()
  const isEdit = !!paiement

  const [typePaiement, setTypePaiement] = useState<'individuel' | 'groupe'>(modeGroupe ? 'groupe' : 'individuel')

  const [idInscription, setIdInscription] = useState<number | ''>('')
  const [idsEcheances, setIdsEcheances] = useState<number[]>([])
  const [montant, setMontant] = useState('')
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10))
  const [mode, setMode] = useState('')
  const [observation, setObservation] = useState('')
  const [error, setError] = useState('')
  const [errors, setErrors] = useState<Errors>({})

  const [idTuteur, setIdTuteur] = useState<number | ''>('')
  const [montantGroupe, setMontantGroupe] = useState('')
  const [remiseDrawerOpen, setRemiseDrawerOpen] = useState(false)
  const [selectedEcheance, setSelectedEcheance] = useState<Echeance | null>(null)
  const [remisesParEcheance, setRemisesParEcheance] = useState<Record<number, RemiseParEcheance>>({})

  useEffect(() => {
    if (open) {
      setTypePaiement(modeGroupe ? 'groupe' : 'individuel')
      setIdInscription(paiement?.id_inscription ?? '')
      setIdsEcheances([])
      setMontant(paiement ? String(paiement.montant) : '')
      setDate(paiement?.date?.slice(0, 10) ?? new Date().toISOString().slice(0, 10))
      setMode(paiement?.mode ?? '')
      setObservation(paiement?.observation ?? '')
      setIdTuteur('')
      setMontantGroupe('')
      setRemisesParEcheance({})
      setError('')
      setErrors({})
    }
  }, [open, paiement, modeGroupe])

  const { data: inscriptions = [], isLoading: loadingInscriptions } = useQuery({
    queryKey: ['inscriptions', 'paiement-combobox'],
    queryFn: () => fetchInscriptions({ limit: 5000 }),
    enabled: open && typePaiement === 'individuel',
  })

  const { data: tuteurs = [], isLoading: loadingTuteurs } = useQuery({
    queryKey: ['tuteurs'],
    queryFn: () => fetchTuteurs(),
    enabled: open && typePaiement === 'groupe',
  })

  const inscriptionId = idInscription !== '' ? Number(idInscription) : null

  const { data: echeances = [], isLoading: loadingEcheances } = useQuery({
    queryKey: ['echeances', inscriptionId],
    queryFn: () => fetchEcheances(inscriptionId!),
    enabled: open && typePaiement === 'individuel' && inscriptionId !== null,
  })

  const echeancesImpayees = echeances.filter((e) => e.statut !== 'SOLDE')
  const resteGlobal = echeancesImpayees.reduce((s, e) => s + e.reste_a_payer, 0)

  const toggleEcheance = (id: number) => {
    setIdsEcheances((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    )
    if (idsEcheances.includes(id)) {
      setRemisesParEcheance((prev) => { const n = { ...prev }; delete n[id]; return n })
    }
  }

  const mutationIndividuel = useMutation<PaiementResult | Paiement>({
    mutationFn: () => isEdit
      ? updatePaiement(paiement.id, {
          montant: Number(montant),
          date,
          mode: mode || null,
          observation: observation || null,
        })
      : createPaiement({
          id_inscription: Number(idInscription),
          ids_echeances: idsEcheances.length > 0 ? idsEcheances : null,
          montant: Number(montant),
          date,
          mode: mode || null,
          observation: observation || null,
          remises: Object.keys(remisesParEcheance).length > 0 ? remisesParEcheance : undefined,
        }),
    onSuccess: (result) => {
      qc.invalidateQueries({ queryKey: ['paiements'] })
      qc.invalidateQueries({ queryKey: ['echeances'] })
      if (isEdit) {
        toast('Paiement modifié.')
      } else {
        const r = result as Awaited<ReturnType<typeof createPaiement>>
        toast(`Paiement enregistré — ${r.nb_paiements_crees} tranche${r.nb_paiements_crees > 1 ? 's' : ''}, reste ${formatMontant(r.reste_global)}.`)
      }
      onClose()
    },
    onError: (err) => setError(extractErrorMessage(err)),
  })

  const mutationGroupe = useMutation<PaiementGroupeResult>({
    mutationFn: () => createPaiementGroupe({
      id_tuteur: Number(idTuteur),
      montant_total: Number(montantGroupe),
      date,
      mode: mode || null,
      observation: observation || null,
    }),
    onSuccess: (result) => {
      qc.invalidateQueries({ queryKey: ['paiements'] })
      qc.invalidateQueries({ queryKey: ['echeances'] })
      toast(`Paiement groupé enregistré — ${result.nb_enfants} enfant${result.nb_enfants > 1 ? 's' : ''}, ${result.nb_paiements_crees} tranche${result.nb_paiements_crees > 1 ? 's' : ''}, reste ${formatMontant(result.reste_total)}.`)
      onClose()
    },
    onError: (err) => setError(extractErrorMessage(err)),
  })

  const handleSubmit = () => {
    if (typePaiement === 'groupe') {
      const errs = validateFields({
        id_tuteur: required(idTuteur, 'Le tuteur'),
        montant: positiveNumber(montantGroupe, 'Le montant'),
        date: required(date, 'La date'),
      })
      setErrors(errs)
      if (hasErrors(errs)) return
      mutationGroupe.mutate()
    } else {
      const errs = validateFields({
        id_inscription: isEdit ? undefined : required(idInscription, "L'élève"),
        montant: positiveNumber(montant, 'Le montant'),
        date: required(date, 'La date'),
      })
      setErrors(errs)
      if (hasErrors(errs)) return
      mutationIndividuel.mutate()
    }
  }

  const isPending = mutationIndividuel.isPending || mutationGroupe.isPending

  return (
    <Drawer open={open} onClose={onClose} title={
      isEdit ? 'Modifier le paiement' : modeGroupe ? 'Paiement groupé' : 'Enregistrer un paiement'
    }>
      <form onSubmit={(e) => { e.preventDefault(); handleSubmit() }} noValidate className="flex flex-col h-full">
        <div className="space-y-4">
          {!isEdit && (
            <div className="flex gap-2 rounded-[var(--radius-sm)] border border-[var(--color-border-soft)] bg-[var(--color-surface-2)] p-1">
              <button
                type="button"
                className={`flex-1 rounded-[var(--radius-xs)] px-3 py-1.5 text-sm font-medium transition-colors ${
                  typePaiement === 'individuel'
                    ? 'bg-[var(--color-brand)] text-white'
                    : 'text-[var(--color-ink-dim)] hover:bg-[var(--color-surface-3)]'
                }`}
                onClick={() => setTypePaiement('individuel')}
              >
                Individuel
              </button>
              <button
                type="button"
                className={`flex-1 rounded-[var(--radius-xs)] px-3 py-1.5 text-sm font-medium transition-colors ${
                  typePaiement === 'groupe'
                    ? 'bg-[var(--color-brand)] text-white'
                    : 'text-[var(--color-ink-dim)] hover:bg-[var(--color-surface-3)]'
                }`}
                onClick={() => setTypePaiement('groupe')}
              >
                Groupe (tuteur)
              </button>
            </div>
          )}

          {typePaiement === 'individuel' ? (
            <>
              {loadingInscriptions ? (
                <div className="flex justify-center py-4"><Spinner /></div>
              ) : (
                <SearchableSelect
                  label="Élève (inscription)"
                  value={idInscription !== '' ? String(idInscription) : ''}
                  onChange={(v) => { setIdInscription(v ? Number(v) : ''); setIdsEcheances([]) }}
                  options={inscriptions.map((i) => ({
                    value: String(i.id),
                    label: `${i.eleve_nom ?? ''} ${i.eleve_prenom ?? ''}`.trim(),
                    sublabel: i.matricule_eleve,
                  }))}
                  placeholder="Rechercher un élève…"
                  emptyMessage="Aucun élève trouvé"
                  disabled={isEdit}
                  error={errors.id_inscription}
                />
              )}

              {!isEdit && inscriptionId && (
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
                          <div className="flex items-center gap-2">
                            {ech.total_remises > 0 && (
                              <span className="text-xs text-[var(--color-success)]">-{formatMontant(ech.total_remises)}</span>
                            )}
                            <span className="font-medium text-[var(--color-ink)]">{formatMontant(ech.reste_a_payer)}</span>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => { setSelectedEcheance(ech); setRemiseDrawerOpen(true) }}
                            >
                              Remise
                            </Button>
                          </div>
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

              {!isEdit && (
              <div>
                <label className="block text-sm font-medium text-[var(--color-ink-dim)]">Mois à payer</label>
                {!inscriptionId ? (
                  <p className="mt-1 text-sm text-[var(--color-ink-faint)]">Sélectionnez d'abord un élève.</p>
                ) : loadingEcheances ? (
                  <div className="mt-2 flex justify-center"><Spinner /></div>
                ) : echeancesImpayees.length === 0 ? (
                  <p className="mt-1 text-sm text-[var(--color-ink-faint)]">Toutes les échéances sont soldées.</p>
                ) : (
                  <div className="mt-1.5 space-y-1.5">
                    {echeancesImpayees.map((ech) => {
                      const checked = idsEcheances.includes(ech.id)
                      const remise = remisesParEcheance[ech.id]
                      return (
                        <div key={ech.id}>
                          <div className="flex items-center gap-3">
                            <input
                              type="checkbox"
                              checked={checked}
                              onChange={() => toggleEcheance(ech.id)}
                              className="accent-[var(--color-brand)]"
                            />
                            <span className="flex-1 text-sm text-[var(--color-ink)]">
                              {ech.type_echeance === 'INSCRIPTION' ? 'Inscription' : ech.mois}
                            </span>
                            {ech.total_remises > 0 && (
                              <span className="text-xs text-[var(--color-success)]">-{formatMontant(ech.total_remises)}</span>
                            )}
                            <span className="text-sm font-medium text-[var(--color-ink)]">
                              {formatMontant(ech.reste_a_payer)}
                            </span>
                          </div>
                          {checked && (
                            <div className="ml-7 mt-1 flex items-center gap-2">
                              <input
                                type="number"
                                min={0}
                                step={100}
                                placeholder="Remise FCFA"
                                value={remise?.montant ?? ''}
                                onChange={(e) => {
                                  const v = Number(e.target.value)
                                  if (v > 0) {
                                    setRemisesParEcheance((prev) => ({
                                      ...prev,
                                      [ech.id]: { montant: v, motif: prev[ech.id]?.motif ?? '' },
                                    }))
                                  } else {
                                    setRemisesParEcheance((prev) => { const n = { ...prev }; delete n[ech.id]; return n })
                                  }
                                }}
                                className="w-28 rounded-[var(--radius-xs)] border border-[var(--color-border-soft)] bg-[var(--color-surface)] px-2 py-0.5 text-xs"
                              />
                              <input
                                type="text"
                                placeholder="Motif"
                                value={remise?.motif ?? ''}
                                onChange={(e) => {
                                  if (remise) {
                                    setRemisesParEcheance((prev) => ({
                                      ...prev,
                                      [ech.id]: { ...prev[ech.id], motif: e.target.value },
                                    }))
                                  }
                                }}
                                className="flex-1 rounded-[var(--radius-xs)] border border-[var(--color-border-soft)] bg-[var(--color-surface)] px-2 py-0.5 text-xs"
                              />
                            </div>
                          )}
                        </div>
                      )
                    })}
                    <p className="pt-1 text-xs text-[var(--color-ink-faint)]">
                      Aucun mois coché = paiement appliqué aux prochaines échéances par défaut.
                    </p>
                  </div>
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
                onChange={(e) => {
                  setMontant(e.target.value)
                  if (errors.montant) setErrors((prev) => ({ ...prev, montant: undefined }))
                }}
                required
                error={errors.montant}
              />
            </>
          ) : (
            <>
              {loadingTuteurs ? (
                <div className="flex justify-center py-4"><Spinner /></div>
              ) : (
                <SearchableSelect
                  label="Tuteur"
                  value={idTuteur !== '' ? String(idTuteur) : ''}
                  onChange={(v) => setIdTuteur(v ? Number(v) : '')}
                  options={tuteurs.map((t) => ({
                    value: String(t.id),
                    label: `${t.nom ?? ''} ${t.prenom ?? ''}`.trim(),
                    sublabel: t.code_tuteur ?? undefined,
                  }))}
                  placeholder="Rechercher un tuteur…"
                  emptyMessage="Aucun tuteur trouvé"
                  error={errors.id_tuteur}
                />
              )}

              <Input
                label="Montant total à répartir (FCFA)"
                type="number"
                min={1}
                step={0.01}
                placeholder="ex. 50000"
                value={montantGroupe}
                onChange={(e) => {
                  setMontantGroupe(e.target.value)
                  if (errors.montant) setErrors((prev) => ({ ...prev, montant: undefined }))
                }}
                required
                error={errors.montant}
              />
              <p className="text-xs text-[var(--color-ink-faint)]">
                Le montant sera divisé équitablement entre les enfants et appliqué aux échéances les plus anciennes.
              </p>
            </>
          )}

          <Input
            label="Date du paiement"
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

          <Select label="Mode de paiement" value={mode} onChange={(e) => setMode(e.target.value)}>
            <option value="">— Non spécifié —</option>
            {MODES.map((m) => <option key={m} value={m}>{m}</option>)}
          </Select>

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
          <Button type="submit" variant="primary" isLoading={isPending}>
            {isEdit ? 'Modifier' : typePaiement === 'groupe' ? 'Enregistrer le groupe' : 'Enregistrer'}
          </Button>
        </div>
      </form>
      <RemiseDrawer
        open={remiseDrawerOpen}
        onClose={() => { setRemiseDrawerOpen(false); setSelectedEcheance(null) }}
        echeance={selectedEcheance}
      />
    </Drawer>
  )
}
