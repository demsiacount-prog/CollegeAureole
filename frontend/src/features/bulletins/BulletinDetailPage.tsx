import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Card, CardBody, CardHeader, CardTitle } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Spinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { Breadcrumbs } from '@/components/ui/PageHeader'
import { formatDate, formatMoyenne } from '@/lib/format'
import { baremeNiveau } from '@/lib/bareme'
import { fetchBulletinDetail } from './api'

function getMoyenneAppreciation(m: number, bareme: number): string {
  const pct = m / bareme
  if (pct >= 0.8) return 'Excellent'
  if (pct >= 0.7) return 'Très bien'
  if (pct >= 0.6) return 'Bien'
  if (pct >= 0.5) return 'Passable'
  return 'Insuffisant'
}

function getMoyenneTone(m: number, bareme: number): 'success' | 'info' | 'warning' | 'danger' {
  const pct = m / bareme
  if (pct >= 0.7) return 'success'
  if (pct >= 0.5) return 'info'
  if (pct >= 0.4) return 'warning'
  return 'danger'
}

export default function BulletinDetailPage() {
  const { id } = useParams<{ id: string }>()

  const { data: bulletin, isLoading, isError } = useQuery({
    queryKey: ['bulletin-detail', id],
    queryFn: () => fetchBulletinDetail(Number(id)),
    enabled: !!id,
  })

  if (isLoading) {
    return (
      <div className="flex justify-center py-24">
        <Spinner label="Chargement du bulletin…" />
      </div>
    )
  }

  if (isError || !bulletin) {
    return <EmptyState message="Impossible de charger ce bulletin." />
  }

  const bareme = baremeNiveau(bulletin.classe.niveau)

  return (
    <div className="flex flex-col gap-6">
      <Breadcrumbs
        items={[
          { label: 'Bulletins', to: '/app/bulletins' },
          { label: `${bulletin.eleve.prenom} ${bulletin.eleve.nom}` },
        ]}
      />

      <Card className="p-6">
        <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-start">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h2 className="text-2xl font-semibold tracking-tight text-[var(--color-ink)]">
                Bulletin — {bulletin.eleve.prenom} {bulletin.eleve.nom}
              </h2>
              <Badge tone={bulletin.statut === 'PUBLIE' ? 'success' : 'neutral'}>
                {bulletin.statut === 'PUBLIE' ? 'Publié' : 'Brouillon'}
              </Badge>
            </div>
            <p className="mt-1 text-sm text-[var(--color-ink-dim)]">
              {bulletin.trimestre.type === 'COMPOSITION' ? 'Composition' : 'Trimestre'} {bulletin.trimestre.nom} — {bulletin.classe.niveau} {bulletin.classe.nom}
            </p>
          </div>
          <div className="text-right">
            <div className="flex items-center gap-2 justify-end">
              <span className="text-3xl font-medium text-[var(--color-ink)]">{formatMoyenne(bulletin.moyenne_generale, bareme)}</span>
              <Badge tone={getMoyenneTone(bulletin.moyenne_generale, bareme)}>
                {getMoyenneAppreciation(bulletin.moyenne_generale, bareme)}
              </Badge>
            </div>
            {bulletin.rang != null && (
              <p className="mt-1 text-sm text-[var(--color-ink-dim)]">Rang {bulletin.rang}ᵉ</p>
            )}
          </div>
        </div>
      </Card>

      {bulletin.appreciation && (
        <Card className="p-5">
          <p className="text-sm text-[var(--color-ink-dim)]">
            <span className="font-medium text-[var(--color-ink)]">Appreciation : </span>
            {bulletin.appreciation}
          </p>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Détail par matière</CardTitle>
        </CardHeader>
        <CardBody>
          {bulletin.details.length === 0 ? (
            <p className="text-sm text-[var(--color-ink-dim)]">Aucun détail disponible.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-[var(--color-border)]">
                    <th className="pb-3 text-left font-medium text-[var(--color-ink-dim)]">Matière</th>
                    <th className="pb-3 text-center font-medium text-[var(--color-ink-dim)]">Coefficient</th>
                    <th className="pb-3 text-center font-medium text-[var(--color-ink-dim)]">Moyenne</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--color-border-soft)]">
                  {bulletin.details.map((d) => (
                    <tr key={d.id}>
                      <td className="py-3 font-medium text-[var(--color-ink)]">{d.cours_nom}</td>
                      <td className="py-3 text-center text-[var(--color-ink-dim)]">{d.coefficient}</td>
                      <td className="py-3 text-center">
                        <Badge tone={getMoyenneTone(d.moyenne, bareme)}>
                          {formatMoyenne(d.moyenne, bareme)}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardBody>
      </Card>

      <div className="text-xs text-[var(--color-ink-faint)]">
        Généré le {formatDate(bulletin.generated_at)}
        {bulletin.published_at && ` · Publié le ${formatDate(bulletin.published_at)}`}
      </div>
    </div>
  )
}
