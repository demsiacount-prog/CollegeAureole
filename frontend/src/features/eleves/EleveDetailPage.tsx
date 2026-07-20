import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { ArrowLeft, Pencil, Phone, MapPin, Briefcase } from 'lucide-react'
import { useAuth } from '@/auth/AuthContext'
import { Card, CardBody, CardHeader, CardTitle } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Avatar } from '@/components/ui/Avatar'
import { Spinner } from '@/components/ui/Spinner'
import { Tabs } from '@/components/ui/Tabs'
import { EmptyState } from '@/components/ui/EmptyState'
import { Button } from '@/components/ui/Button'
import { formatDate, formatMontant, formatMoyenne } from '@/lib/format'
import { fetchDossierEleve, updateEleve } from './api'
import { EleveFormDrawer } from './EleveFormDrawer'

export function EleveDetailPage() {
  const { matricule } = useParams<{ matricule: string }>()
  const { user } = useAuth()
  const canWrite = user?.role === 'admin' || user?.role === 'directeur'
  const [editOpen, setEditOpen] = useState(false)

  const { data: dossier, isLoading, isError, refetch } = useQuery({
    queryKey: ['eleve-dossier', matricule],
    queryFn: () => fetchDossierEleve(matricule!),
    enabled: !!matricule,
  })

  if (isLoading) {
    return (
      <div className="flex justify-center py-24">
        <Spinner label="Chargement du dossier…" />
      </div>
    )
  }

  if (isError || !dossier) {
    return <EmptyState message="Impossible de charger ce dossier élève." />
  }

  return (
    <div className="flex flex-col gap-6">
      <Link to="/app/eleves" className="inline-flex w-fit items-center gap-1.5 text-sm text-[var(--color-ink-dim)] hover:text-[var(--color-ink)]">
        <ArrowLeft className="size-4" />
        Retour aux élèves
      </Link>

      <Card className="p-6">
        <div className="flex flex-col justify-between gap-5 sm:flex-row sm:items-start">
          <div className="flex items-start gap-4">
            <Avatar nom={dossier.nom} prenom={dossier.prenom} size="lg" haloed />
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <h2 className="font-[var(--font-display)] text-2xl font-medium tracking-tight text-[var(--color-ink)]">
                  {dossier.prenom} {dossier.nom}
                </h2>
                <Badge tone={dossier.statut === 'actif' ? 'success' : 'neutral'}>
                  {dossier.statut === 'actif' ? 'Actif' : 'Inactif'}
                </Badge>
              </div>
              <p className="mt-1 font-[var(--font-mono)] text-xs text-[var(--color-ink-faint)]">{dossier.matricule}</p>
              <div className="mt-3 flex flex-wrap gap-x-5 gap-y-1.5 text-sm text-[var(--color-ink-dim)]">
                <span>Né(e) le {formatDate(dossier.date_de_naissance)} à {dossier.lieu_de_naissance}</span>
                <span>{dossier.classe ? `${dossier.classe.niveau} — ${dossier.classe.nom}` : 'Non affecté à une classe'}</span>
              </div>
            </div>
          </div>
          {canWrite && (
            <Button variant="secondary" onClick={() => setEditOpen(true)}>
              <Pencil className="size-4" />
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
            content: <ProfilTab dossier={dossier} />,
          },
          {
            key: 'inscriptions',
            label: `Inscriptions (${dossier.inscriptions.length})`,
            content: <InscriptionsTab inscriptions={dossier.inscriptions} />,
          },
          {
            key: 'notes',
            label: `Notes (${dossier.notes.length})`,
            content: <NotesTab notes={dossier.notes} />,
          },
          {
            key: 'absences',
            label: `Absences (${dossier.absences.length})`,
            content: <AbsencesTab absences={dossier.absences} />,
          },
          {
            key: 'bulletins',
            label: `Bulletins (${dossier.bulletins.length})`,
            content: <BulletinsTab bulletins={dossier.bulletins} />,
          },
        ]}
      />

      <EleveFormDrawer
        open={editOpen}
        onClose={() => setEditOpen(false)}
        eleve={dossier}
        onCreate={async () => {}}
        onUpdate={async (m, payload) => {
          await updateEleve(m, payload)
          await refetch()
        }}
      />
    </div>
  )
}

function ProfilTab({ dossier }: { dossier: import('./types').DossierEleve }) {
  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle>Informations personnelles</CardTitle>
        </CardHeader>
        <CardBody className="flex flex-col gap-2.5 text-sm">
          <Row label="Sexe" value={dossier.sexe === 'M' ? 'Masculin' : 'Féminin'} />
          <Row label="Date de naissance" value={formatDate(dossier.date_de_naissance)} />
          <Row label="Lieu de naissance" value={dossier.lieu_de_naissance} />
          <Row label="Adresse" value={dossier.adresse ?? '—'} />
        </CardBody>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Tuteur</CardTitle>
        </CardHeader>
        <CardBody className="flex flex-col gap-2.5 text-sm">
          <p className="font-medium text-[var(--color-ink)]">
            {dossier.tuteur.prenom} {dossier.tuteur.nom}
          </p>
          <p className="flex items-center gap-2 text-[var(--color-ink-dim)]">
            <Briefcase className="size-3.5 text-[var(--color-ink-faint)]" /> {dossier.tuteur.profession}
          </p>
          <p className="flex items-center gap-2 text-[var(--color-ink-dim)]">
            <Phone className="size-3.5 text-[var(--color-ink-faint)]" /> {dossier.tuteur.telephone}
          </p>
          <p className="flex items-center gap-2 text-[var(--color-ink-dim)]">
            <MapPin className="size-3.5 text-[var(--color-ink-faint)]" /> {dossier.tuteur.adresse}
          </p>
        </CardBody>
      </Card>
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

function InscriptionsTab({ inscriptions }: { inscriptions: import('./types').InscriptionDetail[] }) {
  if (inscriptions.length === 0) return <EmptyState message="Aucune inscription enregistrée." />
  return (
    <div className="flex flex-col gap-3">
      {inscriptions.map((insc) => (
        <Card key={insc.id} className="p-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="font-medium text-[var(--color-ink)]">
                {insc.annee_scolaire?.libelle ?? 'Année inconnue'} — {insc.classe ? `${insc.classe.niveau} ${insc.classe.nom}` : 'Sans classe'}
              </p>
              <p className="mt-0.5 text-xs text-[var(--color-ink-faint)]">Inscrit le {formatDate(insc.date_inscription)}</p>
            </div>
            <Badge tone={insc.statut === 'Inscrit' ? 'success' : insc.statut === 'Exclu' ? 'danger' : 'warning'}>
              {insc.statut}
            </Badge>
          </div>
          <div className="mt-4 grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
            <Stat label="Moyenne annuelle" value={formatMoyenne(insc.moyenne_annuelle)} />
            <Stat label="Absences" value={String(insc.nb_absences)} />
            <Stat label="Montant payé" value={formatMontant(insc.montant_paye)} />
            <Stat label="Reste à payer" value={formatMontant(insc.reste_a_payer)} />
          </div>
        </Card>
      ))}
    </div>
  )
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs text-[var(--color-ink-faint)]">{label}</p>
      <p className="mt-0.5 font-medium text-[var(--color-ink)]">{value}</p>
    </div>
  )
}

function NotesTab({ notes }: { notes: import('./types').NoteEleve[] }) {
  if (notes.length === 0) return <EmptyState message="Aucune note enregistrée." />
  return (
    <div className="overflow-hidden rounded-[var(--radius-lg)] border border-[var(--color-border)]">
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b border-[var(--color-border-soft)] text-xs uppercase tracking-wide text-[var(--color-ink-faint)]">
            <th className="px-4 py-2.5 font-medium">Date</th>
            <th className="px-4 py-2.5 font-medium">Matière</th>
            <th className="px-4 py-2.5 font-medium">Enseignant</th>
            <th className="px-4 py-2.5 font-medium text-right">Note</th>
          </tr>
        </thead>
        <tbody>
          {notes.map((n) => (
            <tr key={n.id} className="border-b border-[var(--color-border-soft)] last:border-0">
              <td className="px-4 py-2.5 text-[var(--color-ink-dim)]">{formatDate(n.date)}</td>
              <td className="px-4 py-2.5 text-[var(--color-ink)]">{n.cours.nom}</td>
              <td className="px-4 py-2.5 text-[var(--color-ink-dim)]">{n.enseignant.prenom} {n.enseignant.nom}</td>
              <td className="px-4 py-2.5 text-right font-medium text-[var(--color-ink)]">{n.note.toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function AbsencesTab({ absences }: { absences: import('./types').AbsenceEleve[] }) {
  if (absences.length === 0) return <EmptyState message="Aucune absence enregistrée." />
  return (
    <div className="overflow-hidden rounded-[var(--radius-lg)] border border-[var(--color-border)]">
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b border-[var(--color-border-soft)] text-xs uppercase tracking-wide text-[var(--color-ink-faint)]">
            <th className="px-4 py-2.5 font-medium">Date</th>
            <th className="px-4 py-2.5 font-medium">Cours</th>
            <th className="px-4 py-2.5 font-medium">Motif</th>
            <th className="px-4 py-2.5 font-medium text-right">Statut</th>
          </tr>
        </thead>
        <tbody>
          {absences.map((a) => (
            <tr key={a.id} className="border-b border-[var(--color-border-soft)] last:border-0">
              <td className="px-4 py-2.5 text-[var(--color-ink-dim)]">{formatDate(a.date_absence)}</td>
              <td className="px-4 py-2.5 text-[var(--color-ink)]">{a.cours?.nom ?? '—'}</td>
              <td className="px-4 py-2.5 text-[var(--color-ink-dim)]">{a.motif ?? '—'}</td>
              <td className="px-4 py-2.5 text-right">
                <Badge tone={a.justifiee ? 'success' : 'danger'}>{a.justifiee ? 'Justifiée' : 'Non justifiée'}</Badge>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function BulletinsTab({ bulletins }: { bulletins: import('./types').BulletinEleve[] }) {
  if (bulletins.length === 0) return <EmptyState message="Aucun bulletin généré." />
  return (
    <div className="flex flex-col gap-3">
      {bulletins.map((b) => (
        <Card key={b.id} className="flex items-center justify-between p-5">
          <div>
            <p className="font-medium text-[var(--color-ink)]">Moyenne générale : {formatMoyenne(b.moyenne_generale)}</p>
            <p className="mt-0.5 text-xs text-[var(--color-ink-faint)]">
              {b.rang ? `Rang ${b.rang} — ` : ''}Généré le {formatDate(b.generated_at)}
            </p>
          </div>
          <Badge tone={b.statut === 'PUBLIE' ? 'halo' : 'neutral'}>{b.statut === 'PUBLIE' ? 'Publié' : 'Brouillon'}</Badge>
        </Card>
      ))}
    </div>
  )
}
