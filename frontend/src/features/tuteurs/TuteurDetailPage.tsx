import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { Pencil, Briefcase } from 'lucide-react'
import { useAuth } from '@/auth/useAuth'
import { Card, CardBody } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Avatar } from '@/components/ui/Avatar'
import { Spinner } from '@/components/ui/Spinner'
import { Tabs } from '@/components/ui/Tabs'
import { EmptyState } from '@/components/ui/EmptyState'
import { Button } from '@/components/ui/Button'
import { Breadcrumbs } from '@/components/ui/PageHeader'
import { DocumentsTab } from '@/features/documents/DocumentsTab'
import { TUTEUR_DOCS_LABELS } from '@/features/documents/labels'
import { fetchDocumentsTuteur, uploadDocumentTuteur } from '@/features/documents/api'
import { formatDate } from '@/lib/format'
import { fetchTuteurById } from './api'
import { TuteurFormDrawer } from './TuteurFormDrawer'

export default function TuteurDetailPage() {
  const { id } = useParams<{ id: string }>()
  const { user } = useAuth()
  const canWrite = user?.role === 'admin' || user?.role === 'directeur'
  const [editOpen, setEditOpen] = useState(false)

  const { data: tuteur, isLoading, isError, refetch } = useQuery({
    queryKey: ['tuteur-detail', id],
    queryFn: () => fetchTuteurById(Number(id)),
    enabled: !!id,
  })

  const { data: documents } = useQuery({
    queryKey: ['tuteur-documents', tuteur?.code_tuteur],
    queryFn: () => fetchDocumentsTuteur(tuteur!.code_tuteur!),
    enabled: !!tuteur?.code_tuteur,
  })

  if (isLoading) {
    return (
      <div className="flex justify-center py-24">
        <Spinner label="Chargement du dossier tuteur…" />
      </div>
    )
  }

  if (isError || !tuteur) {
    return <EmptyState message="Impossible de charger ce dossier tuteur." />
  }

  return (
    <div className="flex flex-col gap-6">
      <Breadcrumbs
        items={[
          { label: 'Tuteurs', to: '/app/tuteurs' },
          { label: `${tuteur.prenom} ${tuteur.nom}` },
        ]}
      />

      <Card className="p-6">
        <div className="flex flex-col justify-between gap-5 sm:flex-row sm:items-start">
          <div className="flex items-start gap-4">
            <Avatar nom={tuteur.nom} prenom={tuteur.prenom} size="lg" highlighted />
            <div>
              <h2 className="text-2xl font-semibold tracking-tight text-[var(--color-ink)]">
                {tuteur.prenom} {tuteur.nom}
              </h2>
              
              <div className="mt-3 flex flex-wrap gap-x-5 gap-y-1.5 text-sm text-[var(--color-ink-dim)]">
               
                <span className="flex items-center gap-1.5">
                  <Briefcase size={14} strokeWidth={1.75} className="text-[var(--color-ink-faint)]" />
                  {tuteur.profession}
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
            key: 'profil',
            label: 'Profil',
            content: (
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <Card>
                  <CardBody className="flex flex-col gap-2.5 text-sm">
                    <Row label="Code tuteur" value={tuteur.code_tuteur ?? '—'} mono />
                    <Row label="Email" value={tuteur.email} />
                    <Row label="Téléphone" value={tuteur.telephone} />
                    <Row label="Profession" value={tuteur.profession} />
                    <Row label="Adresse" value={tuteur.adresse} />
                    <Row label="Inscrit le" value={formatDate(tuteur.created_at)} />
                  </CardBody>
                </Card>
              </div>
            ),
          },
          {
            key: 'eleves',
            label: 'Élèves',
            count: tuteur.eleves.length,
            content: <ElevesTab eleves={tuteur.eleves} />,
          },
          {
            key: 'documents',
            label: 'Documents',
            count: documents?.length ?? 0,
            content: (
              <DocumentsTab
                documents={documents ?? []}
                labels={TUTEUR_DOCS_LABELS}
                invalidateKey={['tuteur-documents', tuteur.code_tuteur ?? '']}
                upload={(typeDocument, file) => uploadDocumentTuteur(tuteur.code_tuteur!, typeDocument, file)}
              />
            ),
          },
        ]}
      />

      <TuteurFormDrawer
        tuteur={tuteur}
        open={editOpen}
        onClose={() => { refetch(); setEditOpen(false) }}
      />
    </div>
  )
}

function Row({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="flex items-center justify-between gap-4 border-b border-[var(--color-border-soft)] py-1.5 last:border-0">
      <span className="text-[var(--color-ink-faint)]">{label}</span>
      <span className={mono ? 'font-[var(--font-mono)] text-xs text-[var(--color-ink)]' : 'text-[var(--color-ink)]'}>
        {value}
      </span>
    </div>
  )
}

function ElevesTab({ eleves }: { eleves: import('@/features/shared/types').EleveResume[] }) {
  if (eleves.length === 0) return <EmptyState message="Aucun élève rattaché à ce tuteur." />
  return (
    <Card>
      <CardBody>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--color-border)]">
                <th className="pb-3 text-left font-medium text-[var(--color-ink-dim)]">Élève</th>
                <th className="pb-3 text-left font-medium text-[var(--color-ink-dim)]">Classe</th>
                <th className="pb-3 text-left font-medium text-[var(--color-ink-dim)]">Date de naissance</th>
                <th className="pb-3 text-left font-medium text-[var(--color-ink-dim)]">Statut</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--color-border-soft)]">
              {eleves.map((e) => (
                <tr key={e.matricule}>
                  <td className="py-3">
                    <Link
                      to={`/app/eleves/${e.matricule}`}
                      className="flex items-center gap-3 text-[var(--color-ink)] hover:text-[var(--color-brand-bright)]"
                    >
                      <Avatar nom={e.nom} prenom={e.prenom} photo={e.photo} size="sm" />
                      <div>
                        <span className="font-medium">{e.prenom} {e.nom}</span>
                      </div>
                    </Link>
                  </td>
                  <td className="py-3 text-[var(--color-ink-dim)]">
                    {e.classe ? `${e.classe.niveau} — ${e.classe.nom}` : '—'}
                  </td>
                  <td className="py-3 text-[var(--color-ink-dim)]">{formatDate(e.date_de_naissance)}</td>
                  <td className="py-3">
                    <Badge tone={e.statut === 'actif' ? 'success' : 'neutral'}>
                      {e.statut === 'actif' ? 'Actif' : 'Inactif'}
                    </Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardBody>
    </Card>
  )
}
