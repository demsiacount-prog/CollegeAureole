import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useParams } from 'react-router-dom'
import { Pencil, BookOpen, GraduationCap } from 'lucide-react'
import { useAuth } from '@/auth/useAuth'
import { Card, CardBody, CardHeader, CardTitle } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Avatar } from '@/components/ui/Avatar'
import { Spinner } from '@/components/ui/Spinner'
import { Tabs } from '@/components/ui/Tabs'
import { EmptyState } from '@/components/ui/EmptyState'
import { Button } from '@/components/ui/Button'
import { Breadcrumbs } from '@/components/ui/PageHeader'
import { DocumentsTab } from '@/features/documents/DocumentsTab'
import { ENSEIGNANT_DOCS_LABELS } from '@/features/documents/labels'
import { fetchDocumentsEnseignant, uploadDocumentEnseignant } from '@/features/documents/api'
import { formatDate } from '@/lib/format'
import { fetchEnseignantDossier } from './api'
import EnseignantFormDrawer from './EnseignantFormDrawer'

export default function EnseignantDetailPage() {
  const { matricule } = useParams<{ matricule: string }>()
  const { user } = useAuth()
  const canWrite = user?.role === 'admin' || user?.role === 'directeur'
  const [editOpen, setEditOpen] = useState(false)

  const { data: dossier, isLoading, isError, refetch } = useQuery({
    queryKey: ['enseignant-dossier', matricule],
    queryFn: () => fetchEnseignantDossier(matricule!),
    enabled: !!matricule,
  })

  const { data: documents } = useQuery({
    queryKey: ['enseignant-documents', matricule],
    queryFn: () => fetchDocumentsEnseignant(matricule!),
    enabled: !!matricule,
  })

  if (isLoading) {
    return (
      <div className="flex justify-center py-24">
        <Spinner label="Chargement du dossier enseignant…" />
      </div>
    )
  }

  if (isError || !dossier) {
    return <EmptyState message="Impossible de charger ce dossier enseignant." />
  }

  const e = dossier.enseignant

  return (
    <div className="flex flex-col gap-6">
      <Breadcrumbs
        items={[
          { label: 'Enseignants', to: '/app/enseignants' },
          { label: `${e.prenom} ${e.nom}` },
        ]}
      />

      <Card className="p-6">
        <div className="flex flex-col justify-between gap-5 sm:flex-row sm:items-start">
          <div className="flex items-start gap-4">
            <Avatar nom={e.nom} prenom={e.prenom} size="lg" highlighted />
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <h2 className="text-2xl font-semibold tracking-tight text-[var(--color-ink)]">
                  {e.prenom} {e.nom}
                </h2>
              </div>
              <div className="mt-3 flex flex-wrap gap-x-5 gap-y-1.5 text-sm text-[var(--color-ink-dim)]">
               
                
                <span className="flex items-center gap-1.5">
                  <GraduationCap size={14} strokeWidth={1.75} className="text-[var(--color-ink-faint)]" />
                  {e.specialite}
                </span>
              </div>
            </div>
          </div>
          {canWrite && (
            <Button variant="secondary" onClick={() => setEditOpen(true)}>
              <Pencil size={16} strokeWidth={1.75} className="mr-1.5" />
              Modifier
            </Button>
          )}
        </div>
      </Card>

      <Tabs
        tabs={[
          {
            key: 'infos',
            label: 'Profil',
            content: (
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <Card>
                  <CardHeader>
                    <CardTitle>Informations personnelles</CardTitle>
                  </CardHeader>
                  <CardBody className="flex flex-col gap-2.5 text-sm">
                    <Row label="Spécialité" value={e.specialite} />
                    <Row label="Email" value={e.email} />
                    <Row label="Téléphone" value={e.telephone} />
                    <Row label="Adresse" value={e.adresse} />
                    <Row label="Quota horaire" value={e.heures_hebdo_max != null ? `${e.heures_hebdo_max}h / semaine` : 'Aucun'} />
                    <Row label="Inscrit le" value={formatDate(e.created_at)} />
                  </CardBody>
                </Card>
              </div>
            ),
          },
          {
            key: 'historique',
            label: 'Historique',
            count: dossier.historique.length,
            content: <HistoriqueTab historique={dossier.historique} />,
          },
          {
            key: 'documents',
            label: 'Documents',
            count: documents?.length ?? 0,
            content: (
              <DocumentsTab
                documents={documents ?? []}
                labels={ENSEIGNANT_DOCS_LABELS}
                invalidateKey={['enseignant-documents', matricule!]}
                upload={(typeDocument, file) => uploadDocumentEnseignant(matricule!, typeDocument, file)}
              />
            ),
          },
        ]}
      />

      <EnseignantFormDrawer
        enseignant={e}
        open={editOpen}
        onClose={() => { refetch(); setEditOpen(false) }}
      />
    </div>
  )
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between border-b border-[var(--color-border-soft)] py-1.5 last:border-0">
      <span className="text-[var(--color-ink-faint)]">{label}</span>
      <span className="text-[var(--color-ink)]">{value}</span>
    </div>
  )
}

function HistoriqueTab({ historique }: { historique: import('./types').AnneeHistorique[] }) {
  if (historique.length === 0) return <EmptyState message="Aucun historique d'affectation." />
  return (
    <div className="flex flex-col gap-4">
      {historique.map((h) => (
        <Card key={h.annee_scolaire?.id ?? 'none'} className="overflow-hidden">
          <div className="border-b border-[var(--color-border-soft)] px-5 py-3">
            <div className="flex items-center gap-2">
              <span className="font-medium text-[var(--color-ink)]">
                {h.annee_scolaire?.libelle ?? 'Année inconnue'}
              </span>
              {h.annee_scolaire?.active && <Badge tone="success">Active</Badge>}
              {h.annee_scolaire?.cloturee && <Badge tone="neutral">Clôturée</Badge>}
            </div>
          </div>
          <CardBody>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-[var(--color-border)]">
                    <th className="pb-2 text-left font-medium text-[var(--color-ink-dim)]">Cours</th>
                    <th className="pb-2 text-left font-medium text-[var(--color-ink-dim)]">Classe</th>
                    <th className="pb-2 text-left font-medium text-[var(--color-ink-dim)]">Volume</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--color-border-soft)]">
                  {h.affectations.map((a, i) => (
                    <tr key={i}>
                      <td className="py-2 text-[var(--color-ink)]">
                        <span className="flex items-center gap-1.5">
                          <BookOpen size={14} strokeWidth={1.75} className="text-[var(--color-ink-faint)]" />
                          {a.cours.nom}
                        </span>
                      </td>
                      <td className="py-2 text-[var(--color-ink-dim)]">
                        {a.classe ? `${a.classe.niveau} — ${a.classe.nom}` : '—'}
                      </td>
                      <td className="py-2 text-[var(--color-ink-dim)]">{a.cours.volume_horaire}h</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardBody>
        </Card>
      ))}
    </div>
  )
}
