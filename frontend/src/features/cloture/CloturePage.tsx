import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { AlertTriangle, ArrowRight, CalendarClock, CheckCircle2, GraduationCap, Repeat, Ban, Clock } from 'lucide-react'
import { Card, CardBody, CardHeader, CardTitle } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { EmptyState } from '@/components/ui/EmptyState'
import { TableSkeleton } from '@/components/ui/TableSkeleton'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { toast } from '@/components/ui/toast'
import { extractErrorMessage } from '@/lib/api'
import { executerCloture, fetchCloturePreview } from './api'
import type { ClotureExecuterResponse } from './types'

const COMPTEUR_CARDS: { key: keyof import('./types').CompteursPreview; label: string; icon: typeof CheckCircle2 }[] = [
  { key: 'ADMIS_PASSAGE', label: 'Admis — passage', icon: ArrowRight },
  { key: 'ADMIS_DIPLOME', label: 'Diplômés (sortie)', icon: GraduationCap },
  { key: 'RECALE_REDOUBLEMENT', label: 'Redoublants', icon: Repeat },
  { key: 'EXCLU', label: 'Exclus', icon: Ban },
  { key: 'EN_ATTENTE', label: 'En attente (bloquant)', icon: Clock },
]

const today = new Date()
const defaultLibelle = `${today.getFullYear()}–${today.getFullYear() + 1}`

export default function CloturePage() {
  const qc = useQueryClient()
  const { data: preview, isLoading, isError, error } = useQuery({ queryKey: ['cloture-preview'], queryFn: fetchCloturePreview })

  const [form, setForm] = useState({
    libelle: defaultLibelle,
    date_debut: `${today.getFullYear()}-09-01`,
    date_fin: `${today.getFullYear() + 1}-07-05`,
  })
  const [confirmOpen, setConfirmOpen] = useState(false)
  const [rapport, setRapport] = useState<ClotureExecuterResponse | null>(null)

  const executerMutation = useMutation({
    mutationFn: () => executerCloture(form),
    onSuccess: (data) => {
      setRapport(data)
      toast('Année scolaire clôturée avec succès.')
      qc.invalidateQueries({ queryKey: ['cloture-preview'] })
      qc.invalidateQueries({ queryKey: ['annees-scolaires'] })
    },
    onError: (e) => toast(extractErrorMessage(e), 'error'),
  })

  if (isLoading) {
    return (
      <Card>
        <TableSkeleton rows={8} columns={5} />
      </Card>
    )
  }

  if (isError || !preview) {
    return (
      <div className="flex flex-col items-center gap-3 rounded-[var(--radius-lg)] border border-[var(--color-warning)]/30 bg-[var(--color-warning-wash)] px-6 py-12 text-center">
        <AlertTriangle className="size-8 text-[var(--color-warning)]" />
        <p className="text-lg font-medium text-[var(--color-ink)]">
          Impossible d'ouvrir la clôture d'année
        </p>
        <p className="max-w-md text-sm text-[var(--color-warning)]">
          {extractErrorMessage(error, "Erreur inconnue lors du chargement de l'aperçu.")}
        </p>
      </div>
    )
  }

  if (rapport) {
    return (
      <Card className="mx-auto max-w-lg p-8 text-center">
        <span className="mx-auto flex size-14 items-center justify-center rounded-full bg-[var(--color-success-wash)]">
          <CheckCircle2 className="size-7 text-[var(--color-success)]" strokeWidth={1.75} />
        </span>
        <h2 className="mt-4 text-xl font-medium text-[var(--color-ink)]">
          Clôture effectuée
        </h2>
        <p className="mt-1.5 text-sm text-[var(--color-ink-dim)]">
          {rapport.ancienne_annee.libelle} est clôturée. {rapport.nouvelle_annee.libelle} est maintenant l'année active.
        </p>
        <div className="mt-6 grid grid-cols-2 gap-3 text-left">
          <Stat label="Admis (passage)" value={rapport.rapport.admis_passage} />
          <Stat label="Diplômés" value={rapport.rapport.admis_diplome} />
          <Stat label="Redoublants" value={rapport.rapport.recale_redoublement} />
          <Stat label="Exclus" value={rapport.rapport.exclus} />
        </div>
      </Card>
    )
  }

  return (
    <div className="flex flex-col gap-5">
      <div>
        <h2 className="text-2xl font-semibold tracking-tight text-[var(--color-ink)]">
          Clôture d'année scolaire
        </h2>
        <p className="mt-1 text-sm text-[var(--color-ink-dim)]">
          {preview.annee_active ? `Année active : ${preview.annee_active.libelle}` : 'Aucune année active.'}
        </p>
      </div>

      

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
        {COMPTEUR_CARDS.map(({ key, label, icon: Icon }) => (
          <Card key={key} className={key === 'EN_ATTENTE' && preview.blocants > 0 ? 'border-[var(--color-danger)]/40 p-4' : 'p-4'}>
            <div className="flex items-center justify-between">
              <p className="text-xs text-[var(--color-ink-dim)]">{label}</p>
              <Icon className="size-4 text-[var(--color-brand)]" strokeWidth={1.75} />
            </div>
            <p className="mt-2 text-2xl font-medium text-[var(--color-ink)]">
              {preview.compteurs[key]}
            </p>
          </Card>
        ))}
      </div>

      {!preview.peut_executer && (
        <div className="flex items-center gap-2 rounded-[var(--radius-md)] border border-[var(--color-warning)]/30 bg-[var(--color-warning-wash)] px-4 py-3 text-sm text-[var(--color-warning)]">
          <AlertTriangle className="size-4 shrink-0" />
          {preview.total_eleves === 0
            ? "Aucune inscription pour l'année active — rien à clôturer."
            : `${preview.blocants} élève(s) encore en attente d'une décision. Réglez-le dans le module Résultats avant de pouvoir exécuter la clôture.`}
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Détail par élève ({preview.total_eleves})</CardTitle>
        </CardHeader>
        <CardBody className="p-0">
          {preview.eleves.length === 0 ? (
            <div className="p-5">
              <EmptyState message="Aucune inscription à prévisualiser." />
            </div>
          ) : (
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-[var(--color-border)] text-sm font-medium text-[var(--color-ink-dim)]">
                  <th className="px-5 py-3 font-medium">Élève</th>
                  <th className="px-5 py-3 font-medium">Classe</th>
                  <th className="px-5 py-3 font-medium">Statut</th>
                  <th className="px-5 py-3 font-medium">Action prévue</th>
                </tr>
              </thead>
              <tbody>
                {preview.eleves.map((e) => (
                  <tr key={e.inscription_id} className="border-b border-[var(--color-border-soft)] last:border-0">
                    <td className="px-5 py-3 font-medium text-[var(--color-ink)]">
                      <Link to={`/app/eleves/${e.matricule}`} className="hover:text-[var(--color-brand-bright)]">
                        {e.prenom} {e.nom}
                      </Link>
                    </td>
                    <td className="px-5 py-3 text-[var(--color-ink-dim)]">
                      {e.classe_nom ? `${e.niveau} — ${e.classe_nom}` : '—'}
                    </td>
                    <td className="px-5 py-3">
                      <Badge tone={e.statut_passage === 'EN_ATTENTE' ? 'danger' : e.statut_passage === 'EXCLU' ? 'warning' : 'success'}>
                        {e.statut_passage}
                      </Badge>
                    </td>
                    <td className="px-5 py-3 text-[var(--color-ink-dim)]">{e.action_prevue}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </CardBody>
      </Card>

      <Card className="p-5">
        <CardTitle className="mb-4 flex items-center gap-2">
          <CalendarClock className="size-4 text-[var(--color-brand)]" />
          Nouvelle année scolaire
        </CardTitle>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          <Input label="Libellé" value={form.libelle} onChange={(e) => setForm({ ...form, libelle: e.target.value })} />
          <Input label="Date de début" type="date" value={form.date_debut} onChange={(e) => setForm({ ...form, date_debut: e.target.value })} />
          <Input label="Date de fin" type="date" value={form.date_fin} onChange={(e) => setForm({ ...form, date_fin: e.target.value })} />
        </div>
        <div className="mt-5 flex justify-end">
          <Button
            variant="danger"
            disabled={!preview.peut_executer}
            isLoading={executerMutation.isPending}
            onClick={() => setConfirmOpen(true)}
          >
            Clôturer l'année et créer {form.libelle || 'la nouvelle année'}
          </Button>
        </div>
      </Card>

      <ConfirmDialog
        open={confirmOpen}
        onClose={() => setConfirmOpen(false)}
        onConfirm={() => {
          setConfirmOpen(false)
          executerMutation.mutate()
        }}
        title="Confirmer la clôture d'année ?"
        description={`${preview.annee_active?.libelle ?? "L'année active"} sera clôturée et verrouillée. ${preview.total_eleves} élève(s) seront traités et "${form.libelle}" deviendra l'année active. Cette action ne peut pas être annulée.`}
        confirmLabel="Clôturer définitivement"
        variant="danger"
      />
    </div>
  )
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-[var(--radius-sm)] border border-[var(--color-border)] px-3 py-2">
      <p className="text-xs text-[var(--color-ink-faint)]">{label}</p>
      <p className="mt-0.5 text-lg font-medium text-[var(--color-ink)]">{value}</p>
    </div>
  )
}
