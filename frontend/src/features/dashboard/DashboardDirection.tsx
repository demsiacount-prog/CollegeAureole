import { useMemo } from 'react'
import { GraduationCap, Wallet, AlertTriangle, Users, BookOpen, CalendarCheck, Clock, UserRound, FilePlus2, Receipt, StickyNote, FileText, type LucideIcon } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { useAuth } from '@/auth/useAuth'
import { Card } from '@/components/ui/Card'
import { EmptyState } from '@/components/ui/EmptyState'
import { PageHeader } from '@/components/ui/PageHeader'
import { fetchDashboardStats } from '@/features/dashboard/api'

const PIE_COLORS = [
  'var(--action)',
  'var(--mod-res)',
  'var(--success)',
  'var(--danger)',
  'var(--info)',
  'var(--warning)',
]

function formatMontant(v: number): string {
  if (v >= 1_000_000) return `${(v / 1_000_000).toFixed(1)}M`
  if (v >= 1_000) return `${(v / 1_000).toFixed(0)}k`
  return v.toLocaleString('fr-FR')
}

function formatDate(iso: string): string {
  const d = new Date(iso)
  return d.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short', year: 'numeric' })
    + ' à ' + d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
}

const ACTIVITY_ICONS: Record<string, LucideIcon> = {
  eleve: UserRound,
  enseignant: GraduationCap,
  tuteur: Users,
  inscription: FilePlus2,
  paiement: Wallet,
  depense: Receipt,
  note: StickyNote,
  absence: AlertTriangle,
  document: FileText,
}

const ACTIVITY_COLORS: Record<string, string> = {
  eleve: 'var(--action)',
  enseignant: 'var(--mod-res)',
  tuteur: 'var(--info)',
  inscription: 'var(--success)',
  paiement: 'var(--success)',
  depense: 'var(--warning)',
  note: 'var(--action)',
  absence: 'var(--danger)',
  document: 'var(--mod-res)',
}

const CHART_TOOLTIP = {
  backgroundColor: 'var(--surface-2)',
  border: '1px solid var(--border)',
  borderRadius: 'var(--radius-md)',
  boxShadow: 'var(--shadow-card)',
  color: 'var(--ink)',
  fontSize: 12.5,
  fontWeight: 500 as const,
  maxWidth: 240,
  padding: '9px 12px',
} as const

/** Style du texte de chaque série dans le tooltip : nom du module (couleur
 *  d'encre) puis valeur en semi-gras — la valeur par défaut gris `#999` de
 *  Recharts est illisible sur fond sombre. */
const CHART_TOOLTIP_ITEM = {
  color: 'var(--ink)',
  fontSize: 12.5,
  padding: 0,
} as const

const CHART_TOOLTIP_LABEL = {
  color: 'var(--ink)',
  fontSize: 12.5,
  fontWeight: 600 as const,
  marginBottom: 5,
} as const

/** Empêche le tooltip d'intercepter le survol : sans `pointer-events: none`,
 *  le pointeur passant sur la bulle fait clignoter le tooltip. */
const CHART_TOOLTIP_WRAPPER = {
  pointerEvents: 'none',
} as const

/** Type J v2 · Dashboard (design system §32 + Type J) :
 *  PageHeader → grille KPI 4 colonnes (bandes de module) → grille de graphiques
 *  (2fr + 1fr) → activité récente pleine largeur. */
export default function DashboardDirection() {
  const { user } = useAuth()
  const { data: stats, isLoading, error } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: fetchDashboardStats,
    refetchInterval: 60_000,
  })

  const absencesCeMois = useMemo(() => {
    if (!stats) return 0
    const m = [...stats.absences_par_mois].reverse().find((a) => a.absences > 0)
    return m?.absences ?? 0
  }, [stats])

  const niveauxTries = useMemo(() => {
    return [...(stats?.repartition_niveaux ?? [])].sort((a, b) => {
      const numA = parseInt(a.name.replace(/\D/g, '')) || 0
      const numB = parseInt(b.name.replace(/\D/g, '')) || 0
      return numA - numB
    })
  }, [stats])

  if (isLoading) {
    return (
      <div className="flex flex-col gap-3">
        <PageHeader title="…" subtitle="Chargement du tableau de bord…" />
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--surface)] p-[14px] shadow-[var(--shadow-card)]">
              <div className="skeleton mb-[8px] h-[11px] w-4/5" />
              <div className="skeleton h-[28px] w-1/2" />
              <div className="skeleton mt-[6px] h-[11px] w-2/3" />
            </div>
          ))}
        </div>
        <div className="grid grid-cols-1 gap-3 xl:grid-cols-3">
          <div className="xl:col-span-2 rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--surface)] p-5 shadow-[var(--shadow-card)]">
            <div className="skeleton mb-4 h-[14px] w-1/3" />
            <div className="skeleton h-[320px] w-full" />
          </div>
          <div className="rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--surface)] p-5 shadow-[var(--shadow-card)]">
            <div className="skeleton mb-4 h-[14px] w-1/2" />
            <div className="skeleton h-[320px] w-full" />
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex h-64 items-center justify-center">
        <p className="text-sm text-[var(--danger)]">
          Impossible de charger les statistiques.
        </p>
      </div>
    )
  }

  const kpis = stats
    ? [
        { label: 'Élèves inscrits', value: stats.nb_eleves.toString(), band: 'band-ped', time: 'Année en cours' },
        { label: 'Enseignants actifs', value: stats.nb_enseignants.toString(), band: 'band-vie', time: 'Année en cours' },
        { label: 'Paiements', value: formatMontant(stats.paiements_annee), band: 'band-fin', time: 'Année en cours' },
        { label: 'Absences du mois', value: absencesCeMois.toString(), band: 'band-res', time: 'Dernier mois relevé' },
      ]
    : []

  return (
    <div className="flex flex-col gap-3">
      <PageHeader
        title={`Bonjour, ${user?.prenom}`}
        subtitle="Voici un aperçu de l'établissement."
      />

      {/* Grille KPI — 4 colonnes, gap 12px */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {kpis.map((kpi) => (
          <div
            key={kpi.label}
            className={`kpi-card ${kpi.band} rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--surface)] p-[14px] shadow-[var(--shadow-card)]`}
          >
            <p className="mb-[5px] text-[10.5px] font-medium uppercase tracking-[0.06em] text-[var(--ink-faint)]">
              {kpi.label}
            </p>
            <p className="font-[var(--font-sans)] text-[26px] font-bold leading-none text-[var(--ink)] tabular-nums">
              {kpi.value}
            </p>
            <p className="mt-[3px] text-[10.5px] text-[var(--ink-faint)]">{kpi.time}</p>
          </div>
        ))}
      </div>

      {stats && (
        <>
          {/* Grille de graphiques — 2fr + 1fr */}
          <div className="grid grid-cols-1 gap-3 xl:grid-cols-3">
            <Card className="min-w-0 xl:col-span-2">
              <div className="flex items-center gap-2 px-5 pt-4">
                <BookOpen className="size-4 text-[var(--action)]" strokeWidth={1.75} />
                <h3 className="text-[15px] font-medium text-[var(--ink)]">Moyennes par classe</h3>
              </div>
              <div className="h-96 max-w-full overflow-x-auto px-2 pb-5 pt-2">
                {stats.moyennes_par_classe.length > 0 ? (
                  <div style={{ minWidth: `${Math.max(stats.moyennes_par_classe.length * 56, 360)}px`, height: '100%' }}>
                    <ResponsiveContainer width="100%" height="100%">
                      {/* EF1 noté /10, EF2 /20 : les barres sont exprimées en % du
                          barème de chaque classe pour rester comparables entre cycles. */}
                      <BarChart data={stats.moyennes_par_classe.map((m) => ({ ...m, pct: m.bareme > 0 ? (m.moy / m.bareme) * 100 : 0 }))}>
                        <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                        <XAxis dataKey="classe" tick={{ fontSize: 12, fill: 'var(--ink-dim)' }} interval={0} angle={-25} textAnchor="end" height={60} />
                        <YAxis domain={[0, 100]} unit="%" tick={{ fontSize: 11, fill: 'var(--ink-dim)' }} />
                        <Tooltip
                          formatter={(_value: unknown, _name: unknown, item: { payload?: { moy?: number; bareme?: number } }) => {
                            const p = item?.payload
                            return [`${p?.moy ?? '—'} / ${p?.bareme ?? '—'}`, 'Moyenne']
                          }}
                          contentStyle={CHART_TOOLTIP}
                          labelStyle={CHART_TOOLTIP_LABEL}
                          itemStyle={CHART_TOOLTIP_ITEM}
                          wrapperStyle={CHART_TOOLTIP_WRAPPER}
                          cursor={{ fill: 'var(--surface-3)' }}
                        />
                        <Bar dataKey="pct" fill="var(--action)" radius={[4, 4, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                ) : (
                  <EmptyState message="Aucune moyenne calculée. Générez des bulletins pour voir les moyennes par classe." />
                )}
              </div>
            </Card>

            <Card>
              <div className="flex items-center gap-2 px-5 pt-4">
                <CalendarCheck className="size-4 text-[var(--danger)]" strokeWidth={1.75} />
                <h3 className="text-[15px] font-medium text-[var(--ink)]">Absences par mois</h3>
              </div>
              <div className="h-96 px-2 pb-5 pt-2">
                {stats.absences_par_mois.some((a) => a.absences > 0) ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={stats.absences_par_mois}>
                      <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                      <XAxis dataKey="mois" tick={{ fontSize: 11, fill: 'var(--ink-dim)' }} angle={-35} textAnchor="end" height={60} />
                      <YAxis tick={{ fontSize: 11, fill: 'var(--ink-dim)' }} />
                      <Tooltip contentStyle={CHART_TOOLTIP} labelStyle={CHART_TOOLTIP_LABEL} itemStyle={CHART_TOOLTIP_ITEM} wrapperStyle={CHART_TOOLTIP_WRAPPER} />
                      <Bar dataKey="absences" fill="var(--danger)" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <EmptyState message="Aucune absence enregistrée sur les derniers mois." />
                )}
              </div>
            </Card>
          </div>

          {/* Répartition des élèves par classe */}
          <Card>
            <div className="flex items-center justify-between gap-2 px-5 pt-4">
              <div className="flex items-center gap-2">
                <UserRound className="size-4 text-[var(--mod-res)]" strokeWidth={1.75} />
                <h3 className="text-[15px] font-medium text-[var(--ink)]">Répartition des élèves</h3>
              </div>
            </div>
            <div className="h-96 px-2 pt-1">
              {niveauxTries.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={niveauxTries}
                      cx="50%"
                      cy="50%"
                      outerRadius={100}
                      dataKey="value"
                      nameKey="name"
                    >
                      {niveauxTries.map((_, index) => (
                        <Cell key={index} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={CHART_TOOLTIP} labelStyle={CHART_TOOLTIP_LABEL} itemStyle={CHART_TOOLTIP_ITEM} wrapperStyle={CHART_TOOLTIP_WRAPPER} />
                    <Legend
                      content={() => (
                        <div className="grid grid-cols-2 gap-x-6 gap-y-2 pt-3 sm:grid-cols-3 xl:grid-cols-6">
                          {niveauxTries.map((item, index) => (
                            <div key={item.name} className="flex items-center gap-2">
                              <span
                                className="inline-block size-3 rounded-[var(--radius-sm)]"
                                style={{ backgroundColor: PIE_COLORS[index % PIE_COLORS.length] }}
                              />
                              <span className="text-[12.5px] text-[var(--ink)]">
                                {item.name.replace(/^Niveau\s*/, '')} · {item.value}
                              </span>
                            </div>
                          ))}
                        </div>
                      )}
                    />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <EmptyState message="Aucune classe ou élève inscrit. Créez des classes et inscrivez des élèves pour voir la répartition." />
              )}
            </div>
          </Card>

          {/* Activité récente — pleine largeur */}
          <Card>
            <div className="flex items-center gap-2 px-5 pt-4">
              <Clock className="size-4 text-[var(--ink-faint)]" strokeWidth={1.75} />
              <h3 className="text-[15px] font-medium text-[var(--ink)]">Activité récente</h3>
            </div>
            <div className="px-5 pb-4 pt-1">
              {stats.dernieres_activites.length > 0 ? (
                <ul className="grid grid-cols-1 gap-x-6 md:grid-cols-2">
                  {stats.dernieres_activites.map((activite, i) => {
                    const Icon = ACTIVITY_ICONS[activite.type] ?? Clock
                    const iconColor = ACTIVITY_COLORS[activite.type] ?? 'var(--ink-faint)'
                    return (
                      <li key={i} className="flex items-center gap-[10px] border-b border-[var(--border-soft)] py-2 last:border-none">
                        <span className="flex size-7 shrink-0 items-center justify-center rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)]">
                          <Icon className="size-[14px]" strokeWidth={1.75} style={{ color: iconColor }} />
                        </span>
                        <div className="min-w-0 flex-1">
                          <p className="truncate text-[13px] text-[var(--ink)]">{activite.texte}</p>
                          <p className="text-[11px] text-[var(--ink-faint)]">{formatDate(activite.date)}</p>
                        </div>
                      </li>
                    )
                  })}
                </ul>
              ) : (
                <EmptyState icon={Clock} message="Aucune activité récente." />
              )}
            </div>
          </Card>
        </>
      )}
    </div>
  )
}