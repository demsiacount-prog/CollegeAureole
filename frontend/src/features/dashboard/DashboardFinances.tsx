import { Wallet, Receipt, Scale, AlertTriangle } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts'
import { useAuth } from '@/auth/useAuth'
import { Card, CardBody, CardHeader, CardTitle } from '@/components/ui/Card'
import { Spinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { fetchDashboardFinances } from './api'

function formatMontant(v: number): string {
  if (v >= 1_000_000) return `${(v / 1_000_000).toFixed(1)}M`
  if (v >= 1_000) return `${(v / 1_000).toFixed(0)}k`
  return v.toLocaleString('fr-FR')
}

function formatMontantPlein(v: number): string {
  return `${v.toLocaleString('fr-FR')} FCFA`
}

function formatDate(iso: string): string {
  const d = new Date(iso)
  return d.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short', year: 'numeric' })
    + ' à ' + d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
}

const ACTIVITY_ICONS: Record<string, React.ComponentType<{ className?: string; strokeWidth?: number }>> = {
  paiement: Wallet,
  depense: Receipt,
}

const ACTIVITY_COLORS: Record<string, string> = {
  paiement: 'text-[var(--color-success)]',
  depense: 'text-[var(--color-warning)]',
}

export default function DashboardFinances() {
  const { user } = useAuth()
  const { data: stats, isLoading, error } = useQuery({
    queryKey: ['dashboard-finances'],
    queryFn: fetchDashboardFinances,
    refetchInterval: 60_000,
  })

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Spinner label="Chargement des flux financiers…" />
      </div>
    )
  }

  if (error || !stats) {
    return (
      <div className="flex h-64 items-center justify-center">
        <p className="text-sm text-[var(--color-danger)]">
          Impossible de charger les flux financiers.
        </p>
      </div>
    )
  }

  const soldePositif = stats.solde_mois >= 0

  const statCards = [
    { label: 'Paiements du mois', period: 'ce mois-ci', icon: Wallet, value: formatMontant(stats.paiements_mois), tone: 'text-[var(--color-success)]' },
    { label: 'Dépenses du mois', period: 'ce mois-ci', icon: Receipt, value: formatMontant(stats.depenses_mois), tone: 'text-[var(--color-warning)]' },
    {
      label: 'Solde du mois',
      period: 'paiements − dépenses',
      icon: Scale,
      value: `${soldePositif ? '+' : ''}${formatMontant(stats.solde_mois)}`,
      tone: soldePositif ? 'text-[var(--color-success)]' : 'text-[var(--color-danger)]',
    },
    { label: 'Échéances en retard', period: `${stats.echeances_en_retard} échéance(s) impayée(s)`, icon: AlertTriangle, value: formatMontant(stats.montant_en_retard), tone: 'text-[var(--color-danger)]' },
  ]

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h2 className="text-2xl font-semibold tracking-tight text-[var(--color-ink)]">
          Bonjour, {user?.prenom}
        </h2>
        <p className="mt-1 text-sm text-[var(--color-ink-dim)]">
          Voici un aperçu des flux financiers de l'établissement.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {statCards.map((stat) => (
          <Card key={stat.label} className="flex flex-col justify-between p-4 min-h-[112px]">
            <div className="flex items-center justify-between gap-2">
              <div className="min-w-0">
                <p className="text-sm font-medium text-[var(--color-ink-dim)]">{stat.label}</p>
                <p className="text-xs text-[var(--color-ink-faint)]">{stat.period}</p>
              </div>
              <stat.icon className={`size-5 shrink-0 ${stat.tone}`} strokeWidth={1.75} />
            </div>
            <p className="mt-3 font-[var(--font-display)] text-3xl font-semibold text-[var(--color-ink)]">
              {stat.value}
            </p>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        <Card className="col-span-1 xl:col-span-2 p-5">
          <div className="mb-4 flex items-center gap-2">
            <Wallet className="size-4 text-[var(--color-brand)]" strokeWidth={1.75} />
            <h3 className="text-[15px] font-medium text-[var(--color-ink)]">
              Paiements et dépenses (6 derniers mois)
            </h3>
          </div>
          <div className="h-96 overflow-x-auto">
            {stats.evolution_mensuelle.some((e) => e.paiements > 0 || e.depenses > 0) ? (
              <div style={{ minWidth: '600px', height: '100%' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={stats.evolution_mensuelle}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                    <XAxis dataKey="mois" tick={{ fontSize: 12, fill: 'var(--color-ink-dim)' }} />
                    <YAxis tick={{ fontSize: 11, fill: 'var(--color-ink-dim)' }} tickFormatter={(v: number) => formatMontant(v)} />
                    <Tooltip
                      formatter={(value) => formatMontantPlein(Number(value))}
                      contentStyle={{
                        backgroundColor: 'var(--color-surface-2)',
                        border: '1px solid var(--color-border)',
                        borderRadius: 'var(--radius-md)',
                        color: 'var(--color-ink)',
                        fontSize: 12,
                      }}
                    />
                    <Legend />
                    <Bar name="Paiements" dataKey="paiements" fill="var(--color-success)" radius={[4, 4, 0, 0]} />
                    <Bar name="Dépenses" dataKey="depenses" fill="var(--color-warning)" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <EmptyState message="Aucun paiement ni dépense enregistré. Les données apparaîtront ici après la première transaction." />
            )}
          </div>
        </Card>
      </div>

      <Card className="flex flex-col">
        <CardHeader>
          <CardTitle>Activité financière récente</CardTitle>
        </CardHeader>
        <CardBody className="flex-1">
          {stats.dernieres_activites.length > 0 ? (
            <ul className="flex max-h-[22rem] flex-col gap-3 overflow-y-auto pr-2">
              {stats.dernieres_activites.map((activite, i) => {
                const Icon = ACTIVITY_ICONS[activite.type] ?? Wallet
                return (
                  <li key={i} className="flex items-start gap-3">
                    <Icon
                      className={`mt-0.5 size-4 shrink-0 ${ACTIVITY_COLORS[activite.type] ?? 'text-[var(--color-ink-faint)]'}`}
                      strokeWidth={1.75}
                    />
                    <div className="min-w-0 flex-1">
                      <p className="text-sm text-[var(--color-ink)]">{activite.texte}</p>
                      <p className="text-xs text-[var(--color-ink-faint)]">{formatDate(activite.date)}</p>
                    </div>
                  </li>
                )
              })}
            </ul>
          ) : (
            <p className="text-sm text-[var(--color-ink-dim)]">Aucune activité financière récente.</p>
          )}
        </CardBody>
      </Card>
    </div>
  )
}
