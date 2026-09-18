import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useParams } from 'react-router-dom'
import { Pencil, BookOpen, GraduationCap, User, History, Files } from 'lucide-react'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Tabs } from '@/components/ui/Tabs'
import { EmptyState } from '@/components/ui/EmptyState'
import { Button } from '@/components/ui/Button'
import { Table, TableBody, TableCell, TableContainer, TableHead, TableHeader, TableRow } from '@/components/ui/Table'
import { InfoSection, InfoField } from '@/components/ui/InfoGrid'
import { DocumentsTab } from '@/features/documents/DocumentsTab'
import { useDocuments } from '@/features/documents/hooks'
import { formatDate } from '@/lib/format'
import { fetchEnseignantDossier } from './api'
import EnseignantFormDrawer from './EnseignantFormDrawer'
import { useLectureSeule } from '@/features/annees_scolaires/useLectureSeule'

export default function EnseignantDetailPage() {
  const { matricule } = useParams<{ matricule: string }>()
  const { lectureSeule } = useLectureSeule()
  const canWrite = !lectureSeule
  const [editOpen, setEditOpen] = useState(false)

  const { data: dossier, isLoading, isError, refetch } = useQuery({
    queryKey: ['enseignant-dossier', matricule],
    queryFn: () => fetchEnseignantDossier(matricule!),
    enabled: !!matricule,
  })

  const { data: documents } = useDocuments('enseignant', matricule ?? '')

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

  if (isError || !dossier) {
    return <EmptyState title="Erreur" message="Impossible de charger ce dossier enseignant." />
  }

  const e = dossier.enseignant

  return (
    <div className="w-full">
      <div className="flex flex-col">
      {/* Type C v2 — Hero band (avatar 48px, nom serif 18px, métadonnées, actions) */}
      <div className="-mx-5 -mt-[18px] flex flex-col gap-4 border-b border-[var(--border)] bg-[var(--surface)] px-5 py-4 sm:flex-row sm:items-center">
        <div className="flex min-w-0 flex-1 items-center gap-4">
          <span className="flex size-[48px] shrink-0 items-center justify-center overflow-hidden rounded-full border-2 border-[var(--border)] bg-[var(--surface-3)] font-[var(--font-sans)] text-[16px] font-semibold text-[var(--ink-dim)]">
            {`${e.prenom.charAt(0)}${e.nom.charAt(0)}`.toUpperCase()}
          </span>
          <div className="min-w-0">
            <h1 className="truncate font-[var(--font-serif)] text-[18px] font-semibold leading-[1.2] text-[var(--ink)]">
              {e.prenom} {e.nom}
            </h1>
            <div className="mt-[3px] flex flex-wrap items-center gap-x-3 gap-y-0.5 text-[11.5px] text-[var(--ink-faint)]">
              <span className="flex items-center gap-1">
                <GraduationCap className="size-3" strokeWidth={1.75} />
                {e.specialite}
              </span>
              <span className="font-[var(--font-mono)] text-[10.5px] capitalize">{e.matricule}</span>
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
            key: 'infos',
            label: 'Profil',
            icon: User,
            content: (
              <div className="gap-5 grid grid-cols-2">
                <InfoSection title="Informations personnelles">
                  <InfoField label="Spécialité" value={e.specialite} />
                  <InfoField label="Genre" value={e.genre === 'M' ? 'Masculin' : e.genre === 'F' ? 'Féminin' : e.genre} />
                  <InfoField label="Date de naissance" value={formatDate(e.date_naissance)} />
                  <InfoField label="Email" value={e.email} />
                  <InfoField label="Téléphone" value={e.telephone} mono />
                  <InfoField label="Adresse" value={e.adresse} />
                  <InfoField label="Matricule" value={e.matricule} mono />
                  <InfoField label="Inscrit le" value={formatDate(e.created_at)} />
                </InfoSection>
                <InfoSection title="Renseignements administratifs">
                  <InfoField label="NINA" value={e.nina} mono />
                  <InfoField label="Catégorie" value={e.categorie} />
                  <InfoField label="Échelon" value={e.echelon} />
                  <InfoField label="Fonction" value={e.fonction} />
                  <InfoField label="Nbre d'enfants (SF)" value={e.sf_nombre_enfants} />
                  <InfoField label="Date de contrat" value={formatDate(e.date_contrat)} />
                  <InfoField label="Date de titularisation" value={formatDate(e.date_titularisation)} />
                  <InfoField label="Dernier avancement" value={formatDate(e.date_dernier_avancement)} />
                  <InfoField label="Classe tenue" value={e.classe_tenue} />
                  <InfoField label="Dernier poste occupé" value={e.dernier_poste} />
                  <InfoField label="Arrivée au CAP" value={formatDate(e.date_arrivee_cap)} />
                  <InfoField label="Diplôme" value={e.diplome} />
                  <div className="col-span-full">
                    <InfoField label="Observations" value={e.observations} />
                  </div>
                </InfoSection>
              </div>
            ),
          },
          {
            key: 'historique',
            label: 'Historique',
            icon: History,
            count: dossier.historique.length,
            content: <HistoriqueTab historique={dossier.historique} />,
          },
          {
            key: 'documents',
            label: 'Documents',
            icon: Files,
            count: documents?.length ?? 0,
            content: (
              <DocumentsTab
                entiteType="enseignant"
                entiteId={matricule!}
                readOnly={!canWrite}
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
          <TableContainer className="rounded-none border-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Cours</TableHead>
                  <TableHead>Classe</TableHead>
                  <TableHead>Volume</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {h.affectations.map((a, i) => (
                  <TableRow key={i}>
                    <TableCell className="text-[var(--color-ink)]">
                      <span className="flex items-center gap-1.5">
                        <BookOpen size={14} strokeWidth={1.75} className="text-[var(--color-ink-faint)]" />
                        {a.cours.nom}
                      </span>
                    </TableCell>
                    <TableCell className="text-[var(--color-ink-dim)]">
                      {a.classe ? `${a.classe.niveau} — ${a.classe.nom}` : '—'}
                    </TableCell>
                    <TableCell className="text-[var(--color-ink-dim)]">{a.cours.volume_horaire}h</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Card>
      ))}
    </div>
  )
}
