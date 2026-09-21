import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useParams, Link } from 'react-router-dom'
import { Pencil, GraduationCap, Cake, User, ClipboardList, UserX, FileText, CreditCard, Files } from 'lucide-react'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Tabs } from '@/components/ui/Tabs'
import { EmptyState } from '@/components/ui/EmptyState'
import { Button } from '@/components/ui/Button'
import { Table, TableBody, TableCell, TableContainer, TableHead, TableHeader, TableRow } from '@/components/ui/Table'
import { InfoSection, InfoField } from '@/components/ui/InfoGrid'
import { formatDate, formatMontant, formatMoyenne } from '@/lib/format'
import { extractErrorMessage } from '@/lib/api'
import { baremeNiveau } from '@/lib/bareme'
import { toast } from '@/components/ui/toast'
import { urlAbsolue } from '@/lib/server'
import { fetchDossierEleve, updateEleve } from './api'
import { EleveFormDrawer } from './EleveFormDrawer'
import InscriptionFormDrawer from '@/features/inscriptions/InscriptionFormDrawer'
import { createInscription } from '@/features/inscriptions/api'
import { DocumentsTab } from '@/features/documents/DocumentsTab'
import { useDocuments } from '@/features/documents/hooks'
import type { DossierEleve, InscriptionDetail, AbsenceEleve, BulletinEleve } from './types'
import { niveauOrdre } from '@/lib/niveaux'
import { FicheSuiviSection } from '@/features/rapports/FicheSuiviSection'
import { useAnneeActive } from '@/features/annees_scolaires/useAnneeActive'
import { FicheMensuelleSection } from '@/features/rapports/FicheMensuelleSection'
import { PiecesClesDossier } from './PiecesClesDossier'

export default function EleveDetailPage() {
  const { matricule } = useParams<{ matricule: string }>()
  const canWrite = true
  const canImportDocs = true
  const [editOpen, setEditOpen] = useState(false)
  const [inscriptionOpen, setInscriptionOpen] = useState(false)

  const { data: anneeActivee } = useAnneeActive()
  const anneeActiveId = anneeActivee?.id

  const { data: dossier, isLoading, isError, refetch } = useQuery({
    queryKey: ['eleve-dossier', matricule, anneeActiveId],
    queryFn: () => fetchDossierEleve(matricule!, anneeActiveId),
    enabled: !!matricule,
  })

  const { data: documentsData } = useDocuments('eleve', matricule ?? '')

  // Un élève déjà inscrit (ou redoublant) pour l'année active n'a plus de
  // bouton « Inscrire » : l'inscription existe déjà.
  const dejaInscritAnneeActive = (dossier?.inscriptions ?? []).some(
    (i) => ['Inscrit', 'Redoublant'].includes(i.statut) && (anneeActiveId == null || i.id_annee_scolaire === anneeActiveId),
  )

  // Le dossier est scopé à l'année active côté backend : `absences` ne
  // contient donc que les absences de l'année courante (pas de regroupement par année).
  const { absences = [] } = dossier ?? {}

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
            <div className="skeleton h-[34px] w-[88px]" />
            <div className="skeleton h-[34px] w-[104px]" />
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
    return <EmptyState title="Erreur" message="Impossible de charger ce dossier élève." />
  }

  return (
    <div className="w-full">
      <div className="flex flex-col">
      {/* Type C v2 — Hero band (fond surface, bordure basse, avatar 48px) */}
      <div className="-mx-5 -mt-[18px] flex flex-col gap-4 border-b border-[var(--border)] bg-[var(--surface)] px-5 py-4 sm:flex-row sm:items-center">
        <div className="flex min-w-0 flex-1 items-center gap-4">
          <span className="flex size-[48px] shrink-0 items-center justify-center overflow-hidden rounded-full border-2 border-[var(--border)] bg-[var(--surface-3)] font-[var(--font-sans)] text-[16px] font-semibold text-[var(--ink-dim)]">
            {dossier.photo ? (
              <img src={urlAbsolue(dossier.photo)} alt="" className="size-full object-cover" />
            ) : (
              `${dossier.prenom.charAt(0)}${dossier.nom.charAt(0)}`.toUpperCase()
            )}
          </span>
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="truncate font-[var(--font-serif)] text-[18px] font-semibold leading-[1.2] text-[var(--ink)]">
                {dossier.prenom} {dossier.nom}
              </h1>
              <Badge tone={dossier.statut === 'actif' ? 'success' : 'neutral'}>
                {dossier.statut === 'actif' ? 'Actif' : 'Inactif'}
              </Badge>
            </div>
            <div className="mt-[3px] flex flex-wrap items-center gap-x-3 gap-y-0.5 text-[11.5px] text-[var(--ink-faint)]">
              <span className="flex items-center gap-1">
                <GraduationCap className="size-3" strokeWidth={1.75} />
                {dossier.classe_annee
                  ? `${dossier.classe_annee.niveau} — ${dossier.classe_annee.nom}`
                  : anneeActiveId != null
                    ? `Non inscrit(e) en ${dossier.annee_scolaire?.libelle ?? "l'année active"}`
                    : 'Non affecté à une classe'}
              </span>
              <span className="flex items-center gap-1">
                <Cake className="size-3" strokeWidth={1.75} />
                Né(e) le {formatDate(dossier.date_de_naissance)}
              </span>
              <span className="font-[var(--font-mono)] text-[10.5px]">{dossier.matricule}</span>
            </div>
          </div>
        </div>
        {canWrite && (
          <div className="flex shrink-0 items-center gap-2">
            {!dejaInscritAnneeActive && (
              <Button variant="primary" onClick={() => setInscriptionOpen(true)}>
                Inscrire
              </Button>
            )}
            <Button variant="secondary" onClick={() => setEditOpen(true)}>
              <Pencil strokeWidth={1.75} className="size-4" />
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
            content: <ProfilTab dossier={dossier} />,
          },
          {
            key: 'inscriptions',
            label: 'Inscriptions',
            icon: ClipboardList,
            count: dossier.inscriptions.length,
            content: <InscriptionsTab inscriptions={dossier.inscriptions} />,
          },
          {
            key: 'absences',
            label: 'Absences',
            icon: UserX,
            count: absences.length,
            content: <AbsencesTab absences={absences} />,
          },
          {
            key: 'bulletins',
            label: 'Bulletins',
            icon: FileText,
            count: dossier.bulletins.length,
            content: <BulletinsTab bulletins={dossier.bulletins} />,
          },
          {
            key: 'documents',
            label: 'Documents',
            icon: Files,
            count: documentsData?.length ?? 0,
            content: (
              <>
                {(() => {
                  const niveau = dossier.classe_annee?.niveau ?? dossier.classe?.niveau
                  return [7, 8, 9].includes(niveauOrdre(niveau) ?? -1) && (
                  <FicheSuiviSection matricule={dossier.matricule} />
                )})()}
                {(() => {
                  const niveau = dossier.classe_annee?.niveau ?? dossier.classe?.niveau
                  const ordre = niveauOrdre(niveau)
                  return ordre != null && ordre >= 1 && ordre <= 6 ? (
                    <FicheMensuelleSection
                      matricule={dossier.matricule}
                      anneeId={anneeActiveId}
                      niveau={niveau}
                    />
                  ) : null
                })()}
                <DocumentsTab
                  entiteType="eleve"
                  entiteId={dossier.matricule}
                  readOnly={!canImportDocs}
                />
              </>
            ),
          },
          {
            key: 'paiements',
            label: 'Paiements',
            icon: CreditCard,
            count: dossier.inscriptions.reduce((somme, i) => somme + i.paiements.length, 0),
            content: <PaiementsTab inscriptions={dossier.inscriptions} />,
          },
        ]}
      />

      <EleveFormDrawer
        open={editOpen}
        onClose={() => setEditOpen(false)}
        eleve={dossier}
        onCreate={async () => {}}
        onUpdate={async (m, payload) => {
          try {
            await updateEleve(m, payload)
            toast('Élève mis à jour')
            await refetch()
          } catch (err) {
            toast(extractErrorMessage(err), 'error')
          }
        }}
        canImport={canImportDocs}
      />

      <InscriptionFormDrawer
        open={inscriptionOpen}
        onClose={() => setInscriptionOpen(false)}
        initialMatricule={dossier.matricule}
        initialAnneeScolaireId={anneeActiveId}
        onSubmit={async (data) => {
          try {
            await createInscription(data)
            toast('Élève inscrit')
            setInscriptionOpen(false)
            await refetch()
          } catch (err) {
            toast(extractErrorMessage(err), 'error')
          }
        }}
      />
      </div>
    </div>
  )
}

function ProfilTab({ dossier }: { dossier: DossierEleve }) {
  return (
    <div>
      <InfoSection title="Informations personnelles">
        <InfoField label="Sexe" value={dossier.sexe === 'M' ? 'Masculin' : 'Féminin'} />
        <InfoField label="Date de naissance" value={formatDate(dossier.date_de_naissance)} mono />
        <InfoField label="Lieu de naissance" value={dossier.lieu_de_naissance ?? '—'} />
        <InfoField label="Père" value={formatParent(dossier.nom_pere, dossier.prenom_pere, dossier.fonction_pere)} />
        <InfoField label="Mère" value={formatParent(dossier.nom_mere, dossier.prenom_mere, dossier.fonction_mere)} />
        <InfoField label="Adresse" value={dossier.adresse ?? '—'} />
      </InfoSection>

      <InfoSection title="Tuteur">
        <InfoField
          label="Tuteur légal"
          value={`${dossier.tuteur.prenom} ${dossier.tuteur.nom}`}
          to={`/app/tuteurs/${dossier.tuteur.id}`}
        />
        <InfoField label="Profession" value={dossier.tuteur.profession ?? '—'} />
        <InfoField label="Téléphone" value={dossier.tuteur.telephone} mono />
        <InfoField label="Adresse" value={dossier.tuteur.adresse} />
      </InfoSection>

      <InfoSection title="Carnet de santé">
        <InfoField label="Carnet de santé" value={dossier.carnet_sante ? 'Présent' : 'À compléter'} />
      </InfoSection>

      <PiecesClesDossier dossier={dossier} />
    </div>
  )
}

function BulletinsTab({ bulletins }: { bulletins: BulletinEleve[] }) {
  if (bulletins.length === 0) return <EmptyState message="Aucun bulletin généré." />
  const sorted = [...bulletins].sort((a, b) => b.id_trimestre - a.id_trimestre)
  return (
    <TableContainer>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Période</TableHead>
            <TableHead className="text-right">Moyenne</TableHead>
            <TableHead className="text-right">Rang</TableHead>
            <TableHead className="text-right">Statut</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {sorted.map((b) => (
            <TableRow key={b.id}>
              <TableCell>
                <Link
                  to={`/app/bulletins/${b.id}`}
                  className="font-medium text-[var(--action)] hover:underline"
                >
                  Trimestre {b.id_trimestre}
                </Link>
              </TableCell>
              <TableCell className="text-right font-medium text-[var(--ink)]">
                {formatMoyenne(b.moyenne_generale, 20)}
              </TableCell>
              <TableCell className="text-right text-[var(--ink-dim)]">
                {b.rang != null ? `${b.rang}ᵉ` : '—'}
              </TableCell>
              <TableCell className="text-right">
                <Badge tone={b.statut === 'PUBLIE' ? 'success' : 'neutral'}>
                  {b.statut === 'PUBLIE' ? 'Publié' : 'Brouillon'}
                </Badge>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  )
}

function PaiementsTab({ inscriptions }: { inscriptions: InscriptionDetail[] }) {
  const paiements = inscriptions.flatMap((insc) => insc.paiements)
  if (paiements.length === 0) return <EmptyState message="Aucun paiement enregistré pour cet élève." />
  const sorted = [...paiements].sort((a, b) => b.date.localeCompare(a.date))
  return (
    <TableContainer>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Date</TableHead>
            <TableHead className="text-left">Code</TableHead>
            <TableHead className="text-right">Montant</TableHead>
            <TableHead className="text-right">Mode</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {sorted.map((p) => (
            <TableRow key={p.id}>
              <TableCell className="font-[var(--font-mono)] text-[11.5px] text-[var(--ink-dim)]">
                {formatDate(p.date)}
              </TableCell>
              <TableCell className="font-[var(--font-mono)] text-[11.5px] text-[var(--ink-dim)]">
                {p.code_paiement ?? '—'}
              </TableCell>
              <TableCell className="text-right font-medium text-[var(--ink)]">
                {formatMontant(p.montant)}
              </TableCell>
              <TableCell className="text-right text-[var(--ink-dim)]">{p.mode ?? '—'}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  )
}

function formatParent(nom: string | null, prenom: string | null, fonction: string | null): string {
  const nomComplet = [nom, prenom].filter(Boolean).join(' ') || '—'
  return fonction ? `${nomComplet} — ${fonction}` : nomComplet
}

function InscriptionsTab({ inscriptions }: { inscriptions: InscriptionDetail[] }) {
  if (inscriptions.length === 0) return <EmptyState message="Aucune inscription enregistrée." />
  return (
    <div className="flex flex-col gap-3">
      {inscriptions.map((insc) => {
        const bm = baremeNiveau(insc.classe?.niveau ?? '')
        return (
        <Card key={insc.id} className="p-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="font-medium text-[var(--ink)]">
                {insc.annee_scolaire?.libelle ?? 'Année inconnue'} — {insc.classe ? `${insc.classe.niveau} ${insc.classe.nom}` : 'Sans classe'}
              </p>
              <p className="mt-0.5 text-xs text-[var(--ink-faint)]">
                {insc.code_inscription ?? `#${insc.id}`} · Inscrit le {formatDate(insc.date_inscription)}
              </p>
            </div>
            <Badge tone={insc.statut === 'Inscrit' ? 'success' : insc.statut === 'Exclu' ? 'danger' : 'warning'}>
              {insc.statut}
            </Badge>
          </div>
          <div className="mt-4 grid grid-cols-2 gap-3 text-sm sm:grid-cols-5">
            <Stat label="Moyenne annuelle" value={formatMoyenne(insc.moyenne_annuelle, bm)} />
            <Stat label="Absences" value={String(insc.nb_absences)} />
            <Stat label="Montant payé" value={formatMontant(insc.montant_paye)} />
            <Stat label="Reste à payer" value={formatMontant(insc.reste_a_payer)} />
            {insc.credit_disponible > 0 && (
              <Stat label="Crédit disponible" value={formatMontant(insc.credit_disponible)} />
            )}
          </div>
        </Card>
      )
    })}
    </div>
  )
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs text-[var(--ink-faint)]">{label}</p>
      <p className="mt-0.5 font-medium text-[var(--ink)]">{value}</p>
    </div>
  )
}

function AbsencesTab({ absences }: { absences: AbsenceEleve[] }) {
  if (absences.length === 0) return <EmptyState message="Aucune absence enregistrée pour l'année active." />
  const sorted = [...absences].sort((a, b) => b.date_absence.localeCompare(a.date_absence))
  return (
    <div className="flex flex-col gap-4">
      <p className="text-xs uppercase tracking-[0.08em] text-[var(--ink-faint)]">
        {sorted.length} absence{sorted.length > 1 ? 's' : ''} — année active
      </p>
      <TableContainer>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Date</TableHead>
              <TableHead>Cours</TableHead>
              <TableHead>Motif</TableHead>
              <TableHead className="text-right">Statut</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {sorted.map((a) => (
              <TableRow key={a.id}>
                <TableCell className="text-[var(--ink-dim)]">{formatDate(a.date_absence)}</TableCell>
                <TableCell className="text-[var(--ink)]">{a.cours?.nom ?? '—'}</TableCell>
                <TableCell className="text-[var(--ink-dim)]">{a.motif ?? '—'}</TableCell>
                <TableCell className="text-right">
                  <Badge tone={a.justifiee ? 'success' : 'danger'}>{a.justifiee ? 'Justifiée' : 'Non justifiée'}</Badge>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </div>
  )
}


