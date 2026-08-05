import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Zap, Info, CheckCircle2, XCircle, Clock, Ban } from 'lucide-react'
import { useAuth } from '@/auth/useAuth'
import { Card, CardBody, CardHeader, CardTitle } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Avatar } from '@/components/ui/Avatar'
import { Select } from '@/components/ui/Select'
import { Button } from '@/components/ui/Button'
import { TableSkeleton } from '@/components/ui/TableSkeleton'
import { EmptyState } from '@/components/ui/EmptyState'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { toast } from '@/components/ui/toast'
import { extractErrorMessage } from '@/lib/api'
import { formatMoyenne } from '@/lib/format'
import { baremeNiveau } from '@/lib/bareme'
import { fetchClasses } from '@/features/classes/api'
import { calculerAutomatiquement, fetchResultatsClasse, modifierStatutPassage } from './api'
import type { RapportAuto, StatutPassage } from './types'

const STATUT_INFO: Record<StatutPassage, { label: string; tone: 'neutral' | 'success' | 'warning' | 'danger'; icon: typeof Clock }> = {
  EN_ATTENTE: { label: 'En attente', tone: 'neutral', icon: Clock },
  ADMIS: { label: 'Admis', tone: 'success', icon: CheckCircle2 },
  RECALE: { label: 'Recalé', tone: 'warning', icon: XCircle },
  EXCLU: { label: 'Exclu', tone: 'danger', icon: Ban },
}

const STATUT_OPTIONS: StatutPassage[] = ['EN_ATTENTE', 'ADMIS', 'RECALE', 'EXCLU']

export default function ResultatListPage() {
  const { user } = useAuth()
  const canDecide = user?.role === 'admin' || user?.role === 'directeur'
  const qc = useQueryClient()

  const { data: classes = [] } = useQuery({ queryKey: ['classes'], queryFn: fetchClasses })
  const [classeId, setClasseId] = useState<number | null>(null)
  const activeClasseId = classeId ?? classes[0]?.id ?? null

  const { data: resultats, isLoading, isError } = useQuery({
    queryKey: ['resultats', activeClasseId],
    queryFn: () => fetchResultatsClasse(activeClasseId!),
    enabled: activeClasseId !== null,
  })

  const [confirmAutoOpen, setConfirmAutoOpen] = useState(false)
  const [rapport, setRapport] = useState<RapportAuto | null>(null)

  const invalidate = () => qc.invalidateQueries({ queryKey: ['resultats', activeClasseId] })

  const autoMutation = useMutation({
    mutationFn: () => calculerAutomatiquement(activeClasseId!),
    onSuccess: (data) => {
      setRapport(data)
      toast('Calcul automatique appliqué.')
      invalidate()
    },
    onError: (e) => toast(extractErrorMessage(e), 'error'),
  })

  const statutMutation = useMutation({
    mutationFn: ({ inscriptionId, statut }: { inscriptionId: number; statut: StatutPassage }) =>
      modifierStatutPassage(inscriptionId, statut),
    onSuccess: () => {
      toast('Statut mis à jour.')
      invalidate()
    },
    onError: (e) => toast(extractErrorMessage(e), 'error'),
  })

  const compteurEntries = useMemo(() => {
    if (!resultats) return []
    return STATUT_OPTIONS.map((s) => ({ statut: s, count: resultats.compteurs[s] ?? 0 }))
  }, [resultats])

  return (
    <div className="flex flex-col gap-5">
      <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight text-[var(--color-ink)]">
            Résultats de passage
          </h2>
          <p className="mt-1 text-sm text-[var(--color-ink-dim)]">
            Décision de passage par élève pour l'année scolaire active.
          </p>
        </div>
        <Select
          value={activeClasseId ?? ''}
          onChange={(e) => setClasseId(Number(e.target.value))}
          options={classes.map((c) => ({ value: c.id, label: `${c.niveau} — ${c.nom}` }))}
          className="w-56"
        />
      </div>

      {isLoading ? (
        <TableSkeleton rows={8} />
      ) : isError || !resultats ? (
        <EmptyState message="Impossible de charger les résultats de cette classe." />
      ) : (
        <>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            {compteurEntries.map(({ statut, count }) => {
              const info = STATUT_INFO[statut]
              return (
                <Card key={statut} className="p-4">
                  <div className="flex items-center justify-between">
                    <p className="text-xs text-[var(--color-ink-dim)]">{info.label}</p>
                    <info.icon className="size-4 text-[var(--color-brand)]" strokeWidth={1.75} />
                  </div>
                  <p className="mt-2 text-2xl font-medium text-[var(--color-ink)]">{count}</p>
                </Card>
              )
            })}
          </div>

          {resultats.niveau_ordre === 9 && (
            <div className="flex items-start gap-2 rounded-[var(--radius-md)] border border-[var(--color-brand-border)] bg-[var(--color-brand-wash)] px-4 py-3 text-sm text-[var(--color-brand)]">
              <Info className="mt-0.5 size-4 shrink-0" />
              <p>Classe de fin de cycle (9ᵉ) : un élève admis ici est marqué diplômé et sort du système lors de la clôture d'année.</p>
            </div>
          )}

          {canDecide && (
            <div className="flex items-center gap-3">
              <Button variant="secondary" onClick={() => setConfirmAutoOpen(true)} isLoading={autoMutation.isPending}>
                <Zap className="size-4" />
                Calculer automatiquement
              </Button>
              <p className="text-xs text-[var(--color-ink-faint)]">
                Applique un seuil de {baremeNiveau(resultats.classe.niveau) / 2}/{baremeNiveau(resultats.classe.niveau)} à tous les élèves non exclus de cette classe. Les décisions déjà prises manuellement restent modifiables ensuite.
              </p>
            </div>
          )}

          {rapport && (
            <Card className="border-[var(--color-brand-border)] p-4">
              <p className="text-sm font-medium text-[var(--color-ink)]">
                Rapport du calcul automatique — seuil {rapport.seuil_applique}/{baremeNiveau(rapport.classe.niveau)}
              </p>
              <p className="mt-1 text-xs text-[var(--color-ink-dim)]">
                {rapport.admis} admis · {rapport.diplomes} diplômé(s) · {rapport.recales} recalé(s) ·{' '}
                {rapport.exclus_conserves} exclu(s) conservé(s) · {rapport.en_attente} toujours en attente
              </p>
            </Card>
          )}

          <Card>
            <CardHeader>
              <CardTitle>Élèves ({resultats.effectif})</CardTitle>
            </CardHeader>
            <CardBody className="p-0">
              {resultats.eleves.length === 0 ? (
                <div className="p-5">
                  <EmptyState message="Aucun élève inscrit dans cette classe pour l'année active." />
                </div>
              ) : (
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr className="border-b border-[var(--color-border)] text-sm font-medium text-[var(--color-ink-dim)]">
                      <th className="px-5 py-3 font-medium">Élève</th>
                      <th className="px-5 py-3 font-medium">Moyenne annuelle</th>
                      <th className="px-5 py-3 font-medium">Statut de passage</th>
                    </tr>
                  </thead>
                  <tbody>
                    {resultats.eleves.map((e) => {
                      const info = STATUT_INFO[e.statut_passage]
                      return (
                        <tr key={e.inscription_id} className="border-b border-[var(--color-border-soft)] last:border-0">
                          <td className="px-5 py-3">
                            <Link to={`/app/eleves/${e.matricule}`} className="flex items-center gap-2.5 group">
                              <Avatar nom={e.nom} prenom={e.prenom} photo={e.photo} size="sm" />
                              <span className="font-medium text-[var(--color-ink)] group-hover:text-[var(--color-brand-bright)]">{e.prenom} {e.nom}</span>
                            </Link>
                          </td>
                          <td className="px-5 py-3 text-[var(--color-ink-dim)]">{formatMoyenne(e.moyenne_annuelle, baremeNiveau(resultats.classe.niveau))}</td>
                          <td className="px-5 py-3">
                            {canDecide ? (
                              <Select
                                value={e.statut_passage}
                                onChange={(ev) =>
                                  statutMutation.mutate({ inscriptionId: e.inscription_id, statut: ev.target.value as StatutPassage })
                                }
                                options={STATUT_OPTIONS.map((s) => ({ value: s, label: STATUT_INFO[s].label }))}
                                className="w-36"
                              />
                            ) : (
                              <Badge tone={info.tone}>{info.label}</Badge>
                            )}
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              )}
            </CardBody>
          </Card>

          <ConfirmDialog
            open={confirmAutoOpen}
            onClose={() => setConfirmAutoOpen(false)}
            onConfirm={() => {
              setConfirmAutoOpen(false)
              autoMutation.mutate()
            }}
            title="Calculer automatiquement les résultats ?"
            description={`Chaque élève non exclu sera marqué admis ou recalé selon sa moyenne annuelle (seuil ${baremeNiveau(resultats.classe.niveau) / 2}/${baremeNiveau(resultats.classe.niveau)}). Cette action modifie directement le statut de passage et peut être ajustée élève par élève ensuite.`}
            confirmLabel="Calculer"
            variant="success"
          />
        </>
      )}
    </div>
  )
}
