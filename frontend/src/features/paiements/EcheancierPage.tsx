import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { ChevronLeft, CreditCard } from 'lucide-react'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { PageHeader, StatChip } from '@/components/ui/PageHeader'
import { EmptyState } from '@/components/ui/EmptyState'
import { TableSkeleton } from '@/components/ui/TableSkeleton'
import { Table, TableBody, TableCell, TableContainer, TableHead, TableHeader, TableRow } from '@/components/ui/Table'
import { fetchEcheances } from './api'
import { fetchInscriptionDetail } from '@/features/inscriptions/api'
import { formatDate, formatMontant } from '@/lib/format'

const STATUT_TONE: Record<string, 'success' | 'warning' | 'danger' | 'info'> = {
  SOLDE: 'success',
  PARTIEL: 'warning',
  EN_ATTENTE: 'info',
  REPORTE: 'danger',
}

const STATUT_LABEL: Record<string, string> = {
  SOLDE: 'Soldée',
  PARTIEL: 'Partielle',
  EN_ATTENTE: 'En attente',
  REPORTE: 'Reportée',
}

export default function EcheancierPage() {
  const { idInscription } = useParams<{ idInscription: string }>()
  const inscriptionId = idInscription ? Number(idInscription) : null

  const { data: detail, isLoading: loadingDetail } = useQuery({
    queryKey: ['inscriptions', 'detail', inscriptionId],
    queryFn: () => fetchInscriptionDetail(inscriptionId!),
    enabled: inscriptionId != null,
  })

  const { data: echeances = [], isLoading: loadingEcheances, isError } = useQuery({
    queryKey: ['echeances', inscriptionId],
    queryFn: () => fetchEcheances(inscriptionId!),
    enabled: inscriptionId != null,
  })

  const totaux = useMemo(() => echeances.reduce(
    (acc, e) => ({
      du: acc.du + e.montant_du,
      paye: acc.paye + e.montant_paye,
      remises: acc.remises + (e.total_remises ?? 0),
      reste: acc.reste + e.reste_a_payer,
    }),
    { du: 0, paye: 0, remises: 0, reste: 0 },
  ), [echeances])

  if (inscriptionId == null) {
    return (
      <div className="w-full py-16">
        <EmptyState title="Inscription inconnue" message="L'identifiant d'inscription est manquant ou invalide." />
      </div>
    )
  }

  if (loadingDetail || loadingEcheances) {
    return (
      <div className="w-full">
        <div className="flex flex-col gap-5">
          <TableSkeleton rows={8} columns={8} />
        </div>
      </div>
    )
  }

  if (isError || !detail) {
    return (
      <div className="w-full py-16">
        <EmptyState title="Erreur" message="Impossible de charger l'échéancier de cette inscription." />
      </div>
    )
  }

  const nomEleve = detail.eleve ? `${detail.eleve.prenom} ${detail.eleve.nom}` : `${detail.eleve_nom ?? ''} ${detail.eleve_prenom ?? ''}`.trim()

  return (
    <div className="w-full">
      <div className="flex flex-col gap-5">
        <div className="flex items-start justify-between">
          <PageHeader
            title="Échéancier"
            count={echeances.length}
            countLabel="échéance(s)"
            breadcrumb={[{ label: 'Paiements', to: '/app/paiements' }, { label: 'Échéancier' }]}
            subtitle={
              <>
                {nomEleve || 'Inscription'} —{' '}
                {detail.code_inscription ?? `n°${inscriptionId}`} —{' '}
                {detail.classe ? `${detail.classe.niveau} — ${detail.classe.nom}` : 'Classe à attribuer'}
                {detail.annee_scolaire ? ` · ${detail.annee_scolaire.libelle}` : ''}
              </>
            }
            summary={
              <>
                <StatChip value={formatMontant(totaux.du)} label="du" />
                <StatChip value={formatMontant(totaux.reste)} label="reste" />
                {detail.credit_disponible > 0 && (
                  <StatChip value={formatMontant(detail.credit_disponible)} label="crédit" />
                )}
              </>
            }
          />
          <Link to="/app/paiements">
            <Button variant="secondary">
              <ChevronLeft size={14} strokeWidth={1.75} className="mr-1.5" />
              Retour aux paiements
            </Button>
          </Link>
        </div>

        {echeances.length === 0 ? (
          <EmptyState
            icon={CreditCard}
            message="Aucune échéance n'a encore été générée pour cette inscription."
          />
        ) : (
          <TableContainer>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Type</TableHead>
                  <TableHead>Mois</TableHead>
                  <TableHead className="text-right">Date d'échéance</TableHead>
                  <TableHead className="text-right">Montant dû</TableHead>
                  <TableHead className="text-right">Payé</TableHead>
                  <TableHead className="text-right">Remises</TableHead>
                  <TableHead className="text-right">Reste</TableHead>
                  <TableHead>Statut</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {echeances.map((ech) => (
                  <TableRow key={ech.id}>
                    <TableCell className="text-[var(--ink-dim)]">
                      {ech.type_echeance === 'INSCRIPTION' ? 'Inscription' : 'Mensualité'}
                    </TableCell>
                    <TableCell className="font-medium text-[var(--ink)]">
                      {ech.mois ?? '—'}
                      {ech.statut === 'REPORTE' && ech.id_echeance_origine != null && (
                        <span className="ml-1.5 text-[11px] font-normal text-[var(--warning)]">(reporté)</span>
                      )}
                    </TableCell>
                    <TableCell className="text-right font-[var(--font-mono)] text-xs text-[var(--ink-dim)]">
                      {formatDate(ech.date_echeance)}
                    </TableCell>
                    <TableCell className="text-right tabular-nums text-[var(--ink)]">
                      {formatMontant(ech.montant_du)}
                    </TableCell>
                    <TableCell className="text-right tabular-nums text-[var(--ink-dim)]">
                      {formatMontant(ech.montant_paye)}
                    </TableCell>
                    <TableCell className="text-right text-[var(--success)]">
                      {ech.total_remises > 0 ? `-${formatMontant(ech.total_remises)}` : '—'}
                    </TableCell>
                    <TableCell className="text-right tabular-nums font-semibold text-[var(--ink)]">
                      {formatMontant(ech.reste_a_payer)}
                    </TableCell>
                    <TableCell>
                      <Badge
                        tone={STATUT_TONE[ech.statut] ?? 'neutral'}
                        title={ech.statut === 'REPORTE' && ech.id_echeance_origine == null
                          ? 'Impayé reporté sur l’année en cours'
                          : undefined}
                      >
                        {STATUT_LABEL[ech.statut] ?? ech.statut}
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
              <tfoot>
                <TableRow className="bg-[var(--surface-2)] hover:bg-[var(--surface-2)] font-medium">
                  <TableCell colSpan={3} className="text-[12.5px] font-semibold text-[var(--ink)]">
                    Total
                  </TableCell>
                  <TableCell className="text-right tabular-nums text-[var(--ink)]">
                    {formatMontant(totaux.du)}
                  </TableCell>
                  <TableCell className="text-right tabular-nums text-[var(--ink)]">
                    {formatMontant(totaux.paye)}
                  </TableCell>
                  <TableCell className="text-right text-[var(--success)]">
                    {totaux.remises > 0 ? `-${formatMontant(totaux.remises)}` : '—'}
                  </TableCell>
                  <TableCell className="text-right tabular-nums font-semibold text-[var(--ink)]">
                    {formatMontant(totaux.reste)}
                  </TableCell>
                  <TableCell />
                </TableRow>
              </tfoot>
            </Table>
          </TableContainer>
        )}
      </div>
    </div>
  )
}