import { GraduationCap, Wallet, CalendarCheck, UserRound, BookOpen, AlertTriangle, Clock, StickyNote } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { useAuth } from '@/auth/AuthContext'
import { Card, CardBody, CardHeader, CardTitle } from '@/components/ui/Card'
import { Spinner } from '@/components/ui/Spinner'
import { fetchDashboardStats } from '@/features/dashboard/api'

const PIE_COLORS = ['#d9a75c', '#3f80a8', '#a3c05c', '#e0707f', '#5b9dc4', '#c98a4a']

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

const ACTIVITY_ICONS = {
  note: StickyNote,
  absence: AlertTriangle,
}

export function DashboardPage() {
  const { user } = useAuth()
  const { data: stats, isLoading, error } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: fetchDashboardStats,
    refetchInterval: 60_000,
  })

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Spinner label="Chargement du tableau de bord…" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex h-64 items-center justify-center">
        <p className="text-sm text-[var(--color-danger)]">
          Impossible de charger les statistiques.
        </p>
      </div>
    )
  }

  const statCards = stats
    ? [
        { label: 'Élèves inscrits', icon: GraduationCap, value: stats.nb_eleves.toString() },
        { label: 'Enseignants actifs', icon: UserRound, value: stats.nb_enseignants.toString() },
        { label: 'Absences (7 jours)', icon: CalendarCheck, value: stats.absences_7_jours.toString() },
        { label: 'Paiements du mois', icon: Wallet, value: formatMontant(stats.paiements_mois) },
      ]
    : []

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h2 className="font-[var(--font-display)] text-2xl font-medium tracking-tight text-[var(--color-ink)]">
          Bonjour, {user?.prenom}
        </h2>
        <p className="mt-1 text-sm text-[var(--color-ink-dim)]">
          Voici un aperçu de l'établissement.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {statCards.map((stat) => (
          <Card key={stat.label} className="flex flex-col justify-between p-6 min-h-[120px]">
            <div className="flex items-center justify-between">
              <p className="text-sm text-[var(--color-ink-dim)]">{stat.label}</p>
              <stat.icon className="size-5 text-[var(--color-halo)]" strokeWidth={1.75} />
            </div>
            <p className="mt-4 font-[var(--font-display)] text-4xl font-medium text-[var(--color-ink)]">
              {stat.value}
            </p>
          </Card>
        ))}
      </div>

      {stats && (
        <>
        <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
          <Card className="col-span-1 xl:col-span-2 p-5">
            <div className="mb-4 flex items-center gap-2">
              <BookOpen className="size-4 text-[var(--color-halo)]" strokeWidth={1.75} />
              <h3 className="font-[var(--font-display)] text-sm font-medium text-[var(--color-ink)]">
                Moyennes par classe
              </h3>
            </div>
            <div className="h-96 overflow-x-auto">
              <div style={{ minWidth: `${Math.max(stats.moyennes_par_classe.length * 80, 500)}px`, height: '100%' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={stats.moyennes_par_classe}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                    <XAxis dataKey="classe" tick={{ fontSize: 12, fill: 'var(--color-ink-dim)' }} interval={0} angle={-25} textAnchor="end" height={60} />
                    <YAxis domain={[0, 20]} tick={{ fontSize: 11, fill: 'var(--color-ink-dim)' }} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: 'var(--color-surface-2)',
                        border: '1px solid var(--color-border)',
                        borderRadius: 'var(--radius-md)',
                        color: 'var(--color-ink)',
                        fontSize: 12,
                      }}
                    />
                    <Bar dataKey="moy" fill="var(--color-halo)" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </Card>

          <Card className="col-span-1 p-5">
            <div className="mb-4 flex items-center gap-2">
              <CalendarCheck className="size-4 text-[var(--color-danger)]" strokeWidth={1.75} />
              <h3 className="font-[var(--font-display)] text-sm font-medium text-[var(--color-ink)]">
                Absences par mois
              </h3>
            </div>
            <div className="h-96">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={stats.absences_par_mois}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                  <XAxis dataKey="mois" tick={{ fontSize: 11, fill: 'var(--color-ink-dim)' }} angle={-35} textAnchor="end" height={60} />
                  <YAxis tick={{ fontSize: 11, fill: 'var(--color-ink-dim)' }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'var(--color-surface-2)',
                      border: '1px solid var(--color-border)',
                      borderRadius: 'var(--radius-md)',
                      color: 'var(--color-ink)',
                      fontSize: 12,
                    }}
                  />
                  <Bar dataKey="absences" fill="var(--color-danger)" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>

        </div>

        <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
          <Card className="p-5">
            <div className="mb-4 flex items-center gap-2">
              <UserRound className="size-4 text-[var(--color-brand-blue)]" strokeWidth={1.75} />
              <h3 className="font-[var(--font-display)] text-sm font-medium text-[var(--color-ink)]">
                Répartition des élèves par classe
              </h3>
            </div>
            <div className="h-96">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={stats.repartition_niveaux}
                    cx="50%"
                    cy="50%"
                    outerRadius={100}
                    dataKey="value"
                    nameKey="name"
                  >
                    {stats.repartition_niveaux.map((_, index) => (
                      <Cell key={index} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'var(--color-surface-2)',
                      border: '1px solid var(--color-border)',
                      borderRadius: 'var(--radius-md)',
                      color: 'var(--color-ink)',
                      fontSize: 12,
                    }}
                  />
                  <Legend
                    content={() => (
                      <div className="grid grid-cols-2 gap-x-6 gap-y-2 pt-3">
                        {[...stats.repartition_niveaux]
                          .sort((a, b) => {
                            const numA = parseInt(a.name.replace(/\D/g, '')) || 0
                            const numB = parseInt(b.name.replace(/\D/g, '')) || 0
                            return numA - numB
                          })
                          .map((item, index) => (
                          <div key={item.name} className="flex items-center gap-2">
                            <span
                              className="inline-block size-3 rounded-sm"
                              style={{ backgroundColor: PIE_COLORS[index % PIE_COLORS.length] }}
                            />
                            <span className="text-sm text-[var(--color-ink)]">
                              {item.name.replace(/^Niveau\s*/, '')} - {item.value} élèves
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </Card>

          <Card className="flex flex-col">
            <CardHeader>
              <CardTitle>Activité récente</CardTitle>
            </CardHeader>
            <CardBody className="flex-1">
              {stats.dernieres_activites.length > 0 ? (
                <ul className="flex flex-col gap-3">
                  {stats.dernieres_activites.map((activite, i) => {
                    const Icon = ACTIVITY_ICONS[activite.type] ?? Clock
                    return (
                      <li key={i} className="flex items-start gap-3">
                        <Icon
                          className={`mt-0.5 size-4 shrink-0 ${
                            activite.type === 'note'
                              ? 'text-[var(--color-halo)]'
                              : 'text-[var(--color-danger)]'
                          }`}
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
                <p className="text-sm text-[var(--color-ink-dim)]">Aucune activité récente.</p>
              )}
            </CardBody>
          </Card>
        </div>
        </>
      )}
    </div>
  )
}
