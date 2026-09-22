import { useEffect, useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import axios from 'axios'
import { Link } from 'react-router-dom'
import { Zap, Info, CheckCircle2, XCircle, Clock, Ban, Lock } from 'lucide-react'
import { Card, CardHeader, CardTitle } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Avatar } from '@/components/ui/Avatar'
import { Select } from '@/components/ui/Select'
import { Button } from '@/components/ui/Button'
import { TableSkeleton } from '@/components/ui/TableSkeleton'
import { Table, TableBody, TableCell, TableContainer, TableHead, TableHeader, TableRow } from '@/components/ui/Table'
import { EmptyState } from '@/components/ui/EmptyState'
import { PageHeader } from '@/components/ui/PageHeader'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { toast } from '@/components/ui/toast'
import { extractErrorMessage } from '@/lib/api'
import { formatMoyenne } from '@/lib/format'
import { baremeNiveau } from '@/lib/bareme'
import { estNiveauJardin } from '@/lib/niveaux'
import { fetchClasses } from '@/features/classes/api'
import { fetchAnneesScolaires } from '@/features/annees_scolaires/api'
import { calculerAutomatiquement, fetchResultatsClasse, modifierStatutPassage } from './api'
import type { RapportAuto, StatutPassage } from './types'

const STATUT_INFO: Record<StatutPassage, { label: string; tone: 'neutral' | 'success' | 'warning' | 'danger'; icon: typeof Clock }> = {
  EN_ATTENTE: { label: 'En attente', tone: 'neutral', icon: Clock },
  ADMIS: { label: 'Admis', tone: 'success', icon: CheckCircle2 },
  RECALE: { label: 'Recalé', tone: 'warning', icon: XCircle },
  EXCLU: { label: 'Exclu', tone: 'danger', icon: Ban },
}

const STATUT_OPTIONS: StatutPassage[] = ['EN_ATTENTE', 'ADMIS', 'RECALE', 'EXCLU']

/** Message du 409 structuré de clôture `{ message, eleves, nb_bloquants }` — la
 *  structure peut être portée par la racine de la réponse ou par `detail`. */
function messageErreur409(e: unknown, fallback: string): string {
  if (axios.isAxiosError(e) && e.response?.status === 409) {
    const data = e.response.data as
      | {
          message?: unknown
          detail?: unknown
          eleves?: unknown[]
          nb_bloquants?: number
        }
      | undefined
    const detail = data?.detail
    const obj =
      detail && typeof detail === 'object'
        ? (detail as { message?: unknown; eleves?: unknown[]; nb_bloquants?: number })
        : ({ ...data } as { message?: unknown; eleves?: unknown[]; nb_bloquants?: number })
    const base =
      typeof obj.message === 'string'
        ? obj.message
        : extractErrorMessage(e, fallback)
    if (typeof obj.nb_bloquants === 'number') {
      return `${base} (${obj.nb_bloquants} élève(s) concerné(s))`
    }
    if (Array.isArray(obj.eleves) && obj.eleves.length > 0) {
      return `${base} (${obj.eleves.length} élève(s) concerné(s))`
    }
    return base
  }
  return extractErrorMessage(e, fallback)
}

export default function ResultatListPage() {
  const qc = useQueryClient()

  const { data: classes = [] } = useQuery({ queryKey: ['classes'], queryFn: fetchClasses })
  const { data: annees = [] } = useQuery({
    queryKey: ['anneesScolaires'],
    queryFn: fetchAnneesScolaires,
  })
  const [classeId, setClasseId] = useState<number | null>(null)
  const [anneeId, setAnneeId] = useState('')
  const activeAnnee = annees.find((a) => a.active)
  useEffect(() => {
    // Année par défaut : l'année active — l'utilisateur reste libre de
    // consulter les années antérieures (archivées) en lecture seule.
    if (activeAnnee && anneeId === '') setAnneeId(String(activeAnnee.id))
  }, [activeAnnee, anneeId])

  const selectedAnnee = annees.find((a) => String(a.id) === anneeId)
  const anneeCloturee = selectedAnnee?.cloturee ?? false

  const activeClasseId = classeId ?? classes[0]?.id ?? null
  const selectedClasse = classes.find((c) => c.id === activeClasseId) ?? null

  const { data: resultats, isLoading, isError } = useQuery({
    queryKey: ['resultats', activeClasseId, anneeId],
    queryFn: () => fetchResultatsClasse(activeClasseId!, anneeId ? Number(anneeId) : undefined),
    enabled: activeClasseId !== null,
  })

  const canDecide = !!resultats?.peut_decider

  const [confirmAutoOpen, setConfirmAutoOpen] = useState(false)
  const [rapport, setRapport] = useState<RapportAuto | null>(null)

  const invalidate = () => qc.invalidateQueries({ queryKey: ['resultats', activeClasseId, anneeId] })

  const autoMutation = useMutation({
    mutationFn: () => calculerAutomatiquement(activeClasseId!),
    onSuccess: (data) => {
      setRapport(data)
      toast('Calcul automatique appliqué.')
      invalidate()
    },
    onError: (e) => toast(messageErreur409(e, 'Impossible de calculer les résultats.'), 'error'),
  })

  const statutMutation = useMutation({
    mutationFn: ({ inscriptionId, statut }: { inscriptionId: number; statut: StatutPassage }) =>
      modifierStatutPassage(inscriptionId, statut),
    onSuccess: () => {
      toast('Statut mis à jour.')
      invalidate()
    },
    onError: (e) => toast(messageErreur409(e, 'Impossible de modifier ce statut.'), 'error'),
  })

  const compteurEntries = useMemo(() => {
    if (!resultats) return []
    return STATUT_OPTIONS.map((s) => ({ statut: s, count: resultats.compteurs[s] ?? 0 }))
  }, [resultats])

  return (
    <div className="flex flex-col gap-5">
      <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
        <PageHeader
          title="Résultats de passage"
          subtitle={
            <p className="mt-1 text-sm text-[var(--ink-dim)]">
              Décision de passage par élève pour l'année scolaire sélectionnée.
            </p>
          }
        />
        <div className="flex flex-wrap items-end gap-3">
          <Select
            label="Année"
            value={anneeId}
            onChange={(e) => setAnneeId(e.target.value)}
            disabled={!annees.length}
            className="w-56"
          >
            <option value="">— Choisir une année —</option>
            {annees.map((a) => (
              <option key={a.id} value={a.id}>
                {a.libelle}{a.cloturee ? ' (archivée)' : ''}
              </option>
            ))}
          </Select>
          <Select
            label="Classe"
            value={activeClasseId ?? ''}
            onChange={(e) => setClasseId(Number(e.target.value))}
            options={classes.map((c) => ({ value: c.id, label: `${c.niveau} — ${c.nom}` }))}
            className="w-56"
            disabled={classes.length === 0}
          />
        </div>
      </div>

      {(anneeCloturee || resultats?.annee_cloturee) && (
        <div className="flex items-start gap-2 rounded-[var(--radius-md)] border border-[var(--action-w)] bg-[var(--action-w)] px-4 py-3 text-sm text-[var(--action)]">
          <Lock className="mt-0.5 size-4 shrink-0" strokeWidth={1.75} />
          <p>
            {selectedAnnee?.libelle ?? "Cette année"} est clôturée : consultation en lecture seule — aucune décision de passage ne peut être modifiée.
          </p>
        </div>
      )}

      {selectedClasse && estNiveauJardin(selectedClasse.niveau) ? (
        <div className="py-16">
          <EmptyState
            title="Pas de passage au jardin d'enfants"
            message="Les résultats de passage ne s'appliquent qu'aux classes du fondamental (1ère à 9ème Année)."
          />
        </div>
      ) : classes.length === 0 ? (
        <div className="py-16">
          <EmptyState message="Aucune classe enregistrée pour le moment." />
        </div>
      ) : isLoading ? (
        <TableSkeleton rows={8} />
      ) : isError || !resultats ? (
        <div className="py-16">
          <EmptyState title="Erreur" message="Impossible de charger les résultats de cette classe." />
        </div>
      ) : (
        <>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            {compteurEntries.map(({ statut, count }) => {
              const info = STATUT_INFO[statut]
              return (
                <Card key={statut} className="p-4">
                  <div className="flex items-center justify-between">
                    <p className="text-xs text-[var(--ink-dim)]">{info.label}</p>
                    <info.icon className="size-4 text-[var(--action)]" strokeWidth={1.75} />
                  </div>
                  <p className="mt-2 text-2xl font-medium text-[var(--ink)]">{count}</p>
                </Card>
              )
            })}
          </div>

          {resultats.niveau_ordre === 9 && (
            <div className="flex items-start gap-2 rounded-[var(--radius-md)] border border-[var(--action-w)] bg-[var(--action-w)] px-4 py-3 text-sm text-[var(--action)]">
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
              <p className="text-xs text-[var(--ink-faint)]">
                Applique un seuil de {baremeNiveau(resultats.classe.niveau) / 2}/{baremeNiveau(resultats.classe.niveau)} à tous les élèves non exclus de cette classe. Les décisions déjà prises manuellement restent modifiables ensuite.
              </p>
            </div>
          )}

          {rapport && (
            <Card className="border-[var(--action-w)] p-4">
             
              <p className="mt-1 text-xs text-[var(--ink-dim)]">
                {rapport.admis} admis · {rapport.diplomes} diplômé(s) · {rapport.recales} recalé(s) ·{' '}
                {rapport.exclus_conserves} exclu(s) conservé(s) · {rapport.en_attente} toujours en attente
              </p>
            </Card>
          )}

          <Card>
            <CardHeader>
              <CardTitle>Élèves ({resultats.effectif})</CardTitle>
            </CardHeader>
            {resultats.eleves.length === 0 ? (
              <div className="p-5">
                <EmptyState message="Aucun élève inscrit dans cette classe pour l'année sélectionnée." />
              </div>
            ) : (
              <TableContainer className="rounded-none border-0">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Élève</TableHead>
                      <TableHead>Moyenne annuelle</TableHead>
                      <TableHead>Statut de passage</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {resultats.eleves.map((e) => {
                      const info = STATUT_INFO[e.statut_passage]
                      return (
                        <TableRow key={e.inscription_id}>
                          <TableCell>
                            <Link to={`/app/eleves/${e.matricule}`} className="flex items-center gap-2.5 group">
                              <Avatar nom={e.nom} prenom={e.prenom} photo={e.photo} size="sm" />
                              <span className="font-medium text-[var(--ink)] group-hover:text-[var(--action-bright)]">{e.prenom} {e.nom}</span>
                            </Link>
                          </TableCell>
                          <TableCell className="text-[var(--ink-dim)]">{formatMoyenne(e.moyenne_annuelle, baremeNiveau(resultats.classe.niveau))}</TableCell>
                          <TableCell>
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
                          </TableCell>
                        </TableRow>
                      )
                    })}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
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
