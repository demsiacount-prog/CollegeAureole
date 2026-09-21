import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { Pencil, Briefcase, User, Users, Files } from 'lucide-react'
import { Badge } from '@/components/ui/Badge'
import { Avatar } from '@/components/ui/Avatar'
import { Tabs } from '@/components/ui/Tabs'
import { EmptyState } from '@/components/ui/EmptyState'
import { Button } from '@/components/ui/Button'
import { Table, TableBody, TableCell, TableContainer, TableHead, TableHeader, TableRow } from '@/components/ui/Table'
import { InfoSection, InfoField } from '@/components/ui/InfoGrid'
import { DocumentsTab } from '@/features/documents/DocumentsTab'
import { formatDate } from '@/lib/format'
import { fetchTuteurById } from './api'
import { TuteurFormDrawer } from './TuteurFormDrawer'
export default function TuteurDetailPage() {
  const { id } = useParams<{ id: string }>()
  const canWrite = true
  const [editOpen, setEditOpen] = useState(false)

  const { data: tuteur, isLoading, isError, refetch } = useQuery({
    queryKey: ['tuteur-detail', id],
    queryFn: () => fetchTuteurById(Number(id)),
    enabled: !!id,
  })

  if (isLoading) {
    return (
      <div className="w-full">
        <div className="-mx-5 -mt-[18px] flex flex-col gap-4 border-b border-[var(--border)] bg-[var(--surface)] px-5 py-4 sm:flex-row sm:items-center">
          <div className="flex min-w-0 flex-1 items-center gap-4">
            <span className="skeleton size-[48px] shrink-0 rounded-full" />
            <div className="min-w-0 flex-1 space-y-2">
              <div className="skeleton h-[18px] w-1/3 max-w-[240px]" />
              <div className="skeleton h-[12px] w-1/2 max-w-[320px]" />
            </div>
          </div>
          <div className="flex shrink-0 items-center gap-2">
            <div className="skeleton h-[34px] w-[120px]" />
          </div>
        </div>
        <div className="border-b border-[var(--border)]">
          <div className="skeleton mt-4 h-[32px] w-64" />
        </div>
        <div className="skeleton mt-6 h-[220px] w-full" />
      </div>
    )
  }

  if (isError || !tuteur) {
    return <EmptyState title="Erreur" message="Impossible de charger ce dossier tuteur." />
  }

  return (
    <div className="w-full">
      <div className="flex flex-col">
      {/* Type C v2 — Hero band (avatar 48px, nom serif 18px, métadonnées, actions) */}
      <div className="-mx-5 -mt-[18px] flex flex-col gap-4 border-b border-[var(--border)] bg-[var(--surface)] px-5 py-4 sm:flex-row sm:items-center">
        <div className="flex min-w-0 flex-1 items-center gap-4">
          <span className="flex size-[48px] shrink-0 items-center justify-center overflow-hidden rounded-full border-2 border-[var(--border)] bg-[var(--surface-3)] font-[var(--font-sans)] text-[16px] font-semibold text-[var(--ink-dim)]">
            {`${tuteur.prenom.charAt(0)}${tuteur.nom.charAt(0)}`.toUpperCase()}
          </span>
          <div className="min-w-0">
            <h1 className="truncate font-[var(--font-serif)] text-[18px] font-semibold leading-[1.2] text-[var(--ink)]">
              {tuteur.prenom} {tuteur.nom}
            </h1>
            <div className="mt-[3px] flex flex-wrap items-center gap-x-3 gap-y-0.5 text-[11.5px] text-[var(--ink-faint)]">
              <span className="flex items-center gap-1">
                <Briefcase className="size-3" strokeWidth={1.75} />
                {tuteur.profession}
              </span>
              {tuteur.code_tuteur && (
                <span className="font-[var(--font-mono)] text-[10.5px]">{tuteur.code_tuteur}</span>
              )}
            </div>
          </div>
        </div>
        {canWrite && (
          <div className="flex shrink-0 items-center gap-2">
            <Button variant="secondary" onClick={() => setEditOpen(true)}>
              <Pencil strokeWidth={1.75} className="mr-1.5 size-4" />
              Modifier
            </Button>
          </div>
        )}
      </div>

      <Tabs
        tabs={[
          {
            key: 'profil',
            label: 'Profil',
            icon: User,
            content: (
              <div className="gap-5 grid grid-cols-2">
                <InfoSection title="Informations personnelles">
                  <InfoField label="Code tuteur" value={tuteur.code_tuteur ?? '—'} mono />
                  <InfoField label="Email" value={tuteur.email} />
                  <InfoField label="Téléphone" value={tuteur.telephone} />
                  <InfoField label="Profession" value={tuteur.profession} />
                  <InfoField label="Adresse" value={tuteur.adresse} />
                  <InfoField label="Inscrit le" value={formatDate(tuteur.created_at)} />
                </InfoSection>
              </div>
            ),
          },
          {
            key: 'eleves',
            label: 'Élèves',
            icon: Users,
            count: tuteur.eleves.length,
            content: <ElevesTab eleves={tuteur.eleves} />,
          },
          {
            key: 'documents',
            label: 'Documents',
            icon: Files,
            content: (
              <DocumentsTab
                entiteType="tuteur"
                entiteId={tuteur.code_tuteur ?? ''}
                readOnly={!canWrite}
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
    </div>
  )
}

function ElevesTab({ eleves }: { eleves: import('@/features/shared/types').EleveResume[] }) {
  if (eleves.length === 0) return <EmptyState message="Aucun élève rattaché à ce tuteur." />
  return (
    <TableContainer>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Élève</TableHead>
            <TableHead>Classe</TableHead>
            <TableHead>Date de naissance</TableHead>
            <TableHead>Statut</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {eleves.map((e) => (
            <TableRow key={e.matricule}>
              <TableCell>
                <Link
                  to={`/app/eleves/${e.matricule}`}
                  className="flex items-center gap-3 text-[var(--ink)] hover:text-[var(--action-bright)]"
                >
                  <Avatar nom={e.nom} prenom={e.prenom} photo={e.photo} size="sm" />
                  <div>
                    <span className="font-medium">{e.prenom} {e.nom}</span>
                  </div>
                </Link>
              </TableCell>
              <TableCell className="text-[var(--ink-dim)]">
                {e.classe ? `${e.classe.niveau} — ${e.classe.nom}` : '—'}
              </TableCell>
              <TableCell className="text-[var(--ink-dim)]">{formatDate(e.date_de_naissance)}</TableCell>
              <TableCell>
                <Badge tone={e.statut === 'actif' ? 'success' : 'neutral'}>
                  {e.statut === 'actif' ? 'Actif' : 'Inactif'}
                </Badge>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  )
}
