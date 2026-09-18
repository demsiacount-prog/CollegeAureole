import { useParams } from 'react-router-dom'
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Download } from 'lucide-react'
import { Card, CardHeader, CardTitle } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { EmptyState } from '@/components/ui/EmptyState'
import { Button } from '@/components/ui/Button'
import { Table, TableBody, TableCell, TableContainer, TableHead, TableHeader, TableRow } from '@/components/ui/Table'
import { Breadcrumbs } from '@/components/ui/PageHeader'
import { formatDate, formatMoyenne } from '@/lib/format'
import { baremeNiveau, appreciation, utiliseCoefficient } from '@/lib/bareme'
import { toast } from '@/components/ui/toast'
import { extractErrorMessage } from '@/lib/api'
import { fetchBulletinDetail, downloadBulletinPdf } from './api'

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

  const [downloading, setDownloading] = useState(false)

  const telecharger = async () => {
    if (!bulletin) return
    setDownloading(true)
    try {
      await downloadBulletinPdf(bulletin.id)
      toast('Bulletin téléchargé.')
    } catch (e) {
      toast(extractErrorMessage(e, 'Impossible de télécharger le bulletin.'), 'error')
    } finally {
      setDownloading(false)
    }
  }

  if (isLoading) {
    return (
      <div className="flex flex-col gap-6">
        <div className="skeleton h-[20px] w-64" />
        <Card className="p-6">
          <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-start">
            <div className="space-y-2">
              <div className="skeleton h-[24px] w-[320px]" />
              <div className="skeleton h-[14px] w-[240px]" />
            </div>
            <div className="space-y-2 text-right">
              <div className="skeleton h-[36px] w-[80px] ml-auto" />
              <div className="skeleton h-[14px] w-[60px] ml-auto" />
            </div>
          </div>
          <div className="skeleton mt-6 h-[180px] w-full" />
        </Card>
      </div>
    )
  }

  if (isError || !bulletin) {
    return <EmptyState title="Erreur" message="Impossible de charger ce bulletin." />
  }

  const bareme = baremeNiveau(bulletin.classe.niveau)
  // Colonnes Coeff / Note×Coeff présentes quand le bulletin est pondéré :
  // EF2/lycée (trimestres /20) et TRIMESTRES de la 6ème (pondérés sur /10).
  const montreCoeff = utiliseCoefficient(bulletin.classe.niveau, bulletin.trimestre.type)

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
              <h2 className="font-[var(--font-serif)] text-2xl font-semibold tracking-tight text-[var(--color-ink)]">
                Bulletin — {bulletin.eleve.prenom} {bulletin.eleve.nom}
              </h2>
              <Badge tone={bulletin.statut === 'PUBLIE' ? 'success' : 'neutral'}>
                {bulletin.statut === 'PUBLIE' ? 'Publié' : 'Brouillon'}
              </Badge>
            </div>
            <p className="mt-1 text-sm text-[var(--color-ink-dim)]">
              {bulletin.trimestre.nom} — {bulletin.classe.niveau} {bulletin.classe.nom}
            </p>
          </div>
          <div className="text-right">
            <div className="flex items-center gap-2 justify-end">
              <span className="text-3xl font-medium text-[var(--color-ink)]">{formatMoyenne(bulletin.moyenne_generale, bareme)}</span>
              <Badge tone={getMoyenneTone(bulletin.moyenne_generale, bareme)}>
                {bulletin.moyenne_generale != null ? appreciation(bulletin.moyenne_generale, bareme) : '—'}
              </Badge>
            </div>
            {bulletin.rang != null && (
              <p className="mt-1 text-sm text-[var(--color-ink-dim)]">Rang {bulletin.rang}{bulletin.rang === 1 ? 'er' : 'e'}</p>
            )}
            <div className="mt-3 flex justify-end">
              <Button variant="primary" isLoading={downloading} onClick={telecharger} className="shrink-0">
                <Download size={14} strokeWidth={1.75} className="mr-1.5" />
                Télécharger le PDF
              </Button>
            </div>
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
        {bulletin.details.length === 0 ? (
          <p className="p-5 text-sm text-[var(--color-ink-dim)]">Aucun détail disponible.</p>
        ) : (
          <TableContainer className="rounded-none border-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Matière</TableHead>
                  {/* Pondéré (trimestre EF2/lycée ou 6ème) : Coefficient / Moyenne / Note × Coeff.
                      EF1 en composition (moyenne simple) : seule la moyenne. */}
                  {montreCoeff ? (
                    <>
                      <TableHead className="text-center">Coefficient</TableHead>
                      <TableHead className="text-center">Moyenne</TableHead>
                      <TableHead className="text-center">Note × Coefficient</TableHead>
                    </>
                  ) : (
                    <TableHead className="text-center">Moyenne</TableHead>
                  )}
                </TableRow>
              </TableHeader>
              <TableBody>
                {bulletin.details.map((d) => (
                  <TableRow key={d.id}>
                    <TableCell className="font-medium text-[var(--color-ink)]">{d.cours_nom}</TableCell>
                    {montreCoeff ? (
                      <>
                        <TableCell className="text-center text-[var(--color-ink-dim)]">{d.coefficient}</TableCell>
                        <TableCell className="text-center">
                          <Badge tone={getMoyenneTone(d.moyenne, bareme)}>
                            {formatMoyenne(d.moyenne, bareme)}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-center font-medium text-[var(--color-ink)]">
                          {(d.moyenne * d.coefficient).toFixed(2)}
                        </TableCell>
                      </>
                    ) : (
                      <TableCell className="text-center">
                        <Badge tone={getMoyenneTone(d.moyenne, bareme)}>
                          {formatMoyenne(d.moyenne, bareme)}
                        </Badge>
                      </TableCell>
                    )}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Card>

      <div className="text-xs text-[var(--color-ink-faint)]">
        Généré le {formatDate(bulletin.generated_at)}
        {bulletin.published_at && ` · Publié le ${formatDate(bulletin.published_at)}`}
      </div>
    </div>
  )
}
