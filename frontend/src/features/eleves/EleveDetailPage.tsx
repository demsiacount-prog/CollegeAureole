import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useParams, Link } from 'react-router-dom'
import { Pencil, GraduationCap, Cake, ChevronDown, User, ClipboardList, UserX, FileText, CreditCard, Files } from 'lucide-react'
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
import { FicheMensuelleSection } from '@/features/rapports/FicheMensuelleSection'
import { PiecesClesDossier } from './PiecesClesDossier'

export default function EleveDetailPage() {
  const { matricule } = useParams<{ matricule: string }>()
  const canWrite = true
  const canImportDocs = true
  const [editOpen, setEditOpen] = useState(false)
  const [inscriptionOpen, setInscriptionOpen] = useState(false)

  const { data: dossier, isLoading, isError, refetch } = useQuery({
    queryKey: ['eleve-dossier', matricule],
    queryFn: () => fetchDossierEleve(matricule!),
    enabled: !!matricule,
  })

  const { data: documentsData } = useDocuments('eleve', matricule ?? '')

  const anneeActiveId = dossier?.annee_scolaire?.id
  // Un élève déjà inscrit (ou redoublant) pour l'année active n'a plus de
  // bouton « Inscrire » : l'inscription existe déjà.
  const dejaInscritAnneeActive = (dossier?.inscriptions ?? []).some(
    (i) => ['Inscrit', 'Redoublant'].includes(i.statut) && (anneeActiveId == null || i.id_annee_scolaire === anneeActiveId),
  )

  const anneesRanges = useMemo(() => {
    const seen = new Map<number, { id: number; libelle: string; dateDebut: string; dateFin: string }>()
    for (const insc of dossier?.inscriptions ?? []) {
      const y = insc.annee_scolaire
      if (!y || seen.has(y.id)) continue
      seen.set(y.id, { id: y.id, libelle: y.libelle, dateDebut: y.date_debut, dateFin: y.date_fin })
    }
    return [...seen.values()]
  }, [dossier])

  const absencesParAnnee = useMemo(
    () => regrouperAbsences(dossier?.absences ?? [], anneesRanges, anneeActiveId ?? null),
    [dossier, anneesRanges, anneeActiveId],
  )
  const nbAbsencesActives =
    anneeActiveId != null
      ? (absencesParAnnee.find((g) => g.anneeId === anneeActiveId)?.absences.length ?? 0)
      : 0
  const anneeAbsencesDefaut = absencesParAnnee[0]?.anneeId ?? null

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
                {dossier.classe ? `${dossier.classe.niveau} — ${dossier.classe.nom}` : 'Non affecté à une classe'}
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
            count: nbAbsencesActives,
            content: <AbsencesTab groups={absencesParAnnee} defaultExpandedId={anneeAbsencesDefaut} />,
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
                {[7, 8, 9].includes(niveauOrdre(dossier.classe?.niveau) ?? -1) && (
                  <FicheSuiviSection matricule={dossier.matricule} />
                )}
                {(() => {
                  const ordre = niveauOrdre(dossier.classe?.niveau)
                  return ordre != null && ordre >= 1 && ordre <= 6 ? (
                    <FicheMensuelleSection
                      matricule={dossier.matricule}
                      anneeId={anneeActiveId}
                      niveau={dossier.classe?.niveau}
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
                  className="font-medium text-[var(--color-action)] hover:underline"
                >
                  Trimestre {b.id_trimestre}
                </Link>
              </TableCell>
              <TableCell className="text-right font-medium text-[var(--color-ink)]">
                {formatMoyenne(b.moyenne_generale, 20)}
              </TableCell>
              <TableCell className="text-right text-[var(--color-ink-dim)]">
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
              <TableCell className="font-[var(--font-mono)] text-[11.5px] text-[var(--color-ink-dim)]">
                {formatDate(p.date)}
              </TableCell>
              <TableCell className="font-[var(--font-mono)] text-[11.5px] text-[var(--color-ink-dim)]">
                {p.code_paiement ?? '—'}
              </TableCell>
              <TableCell className="text-right font-medium text-[var(--color-ink)]">
                {formatMontant(p.montant)}
              </TableCell>
              <TableCell className="text-right text-[var(--color-ink-dim)]">{p.mode ?? '—'}</TableCell>
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
              <p className="font-medium text-[var(--color-ink)]">
                {insc.annee_scolaire?.libelle ?? 'Année inconnue'} — {insc.classe ? `${insc.classe.niveau} ${insc.classe.nom}` : 'Sans classe'}
              </p>
              <p className="mt-0.5 text-xs text-[var(--color-ink-faint)]">
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
      <p className="text-xs text-[var(--color-ink-faint)]">{label}</p>
      <p className="mt-0.5 font-medium text-[var(--color-ink)]">{value}</p>
    </div>
  )
}

interface AnneeAbsences {
  anneeId: number
  libelle: string
  absences: AbsenceEleve[]
}

function regrouperAbsences(
  absences: AbsenceEleve[],
  anneesRanges: { id: number; libelle: string; dateDebut: string; dateFin: string }[],
  anneeActiveId: number | null,
): AnneeAbsences[] {
  const groupes = new Map<number, AnneeAbsences>()
  for (const a of absences) {
    const match = anneesRanges.find(
      (y) => y.dateDebut && y.dateFin && a.date_absence >= y.dateDebut && a.date_absence <= y.dateFin,
    )
    const anneeId = match ? match.id : -1
    const libelle = match ? match.libelle : 'Année inconnue'
    if (!groupes.has(anneeId)) groupes.set(anneeId, { anneeId, libelle, absences: [] })
    groupes.get(anneeId)!.absences.push(a)
  }
  const active = anneesRanges.find((y) => y.id === anneeActiveId)
  if (active && !groupes.has(active.id)) {
    groupes.set(active.id, { anneeId: active.id, libelle: active.libelle, absences: [] })
  }
  return [...groupes.values()].sort((a, b) => {
    if (a.anneeId === anneeActiveId) return -1
    if (b.anneeId === anneeActiveId) return 1
    return (b.absences[0]?.date_absence ?? '').localeCompare(a.absences[0]?.date_absence ?? '')
  })
}

function AbsencesTab({ groups, defaultExpandedId }: { groups: AnneeAbsences[]; defaultExpandedId: number | null }) {
  const [expanded, setExpanded] = useState<Set<number>>(
    () => new Set(defaultExpandedId != null ? [defaultExpandedId] : []),
  )

  const total = groups.reduce((somme, g) => somme + g.absences.length, 0)
  if (total === 0) return <EmptyState message="Aucune absence enregistrée." />

  const toggle = (id: number) =>
    setExpanded((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })

  return (
    <div className="flex flex-col gap-4">
      {groups.map((g) => {
       
        const ouvert = expanded.has(g.anneeId)
        return (
          <div key={g.anneeId} className="flex flex-col gap-3">
            <button
              type="button"
              onClick={() => toggle(g.anneeId)}
              className="flex w-full items-center justify-between gap-3 rounded-[var(--radius-lg)] border border-[var(--color-border)] bg-[var(--color-surface-1)] px-4 py-3 text-left transition-colors hover:bg-[var(--color-surface-2)]"
            >
              <div className="flex flex-wrap items-center gap-2">
                <h4 className="font-medium text-[var(--color-ink)]">{g.libelle}</h4>
                <Badge tone={g.absences.length > 0 ? 'warning' : 'success'} className="text-xs">
                  {g.absences.length} absence{g.absences.length > 1 ? 's' : ''}
                </Badge>
              </div>
              <ChevronDown
                strokeWidth={1.75}
                className={`size-4 shrink-0 text-[var(--color-ink-faint)] transition-transform ${ouvert ? 'rotate-180' : ''}`}
              />
            </button>
            {ouvert &&
              (g.absences.length === 0 ? (
                <p className="px-2 text-sm text-[var(--color-ink-faint)]">Aucune absence pour l'année active.</p>
              ) : (
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
                    
                      {g.absences.map((a) => (
                      
                        <TableRow key={a.id}>
                          
                          <TableCell className="text-[var(--color-ink-dim)]">{formatDate(a.date_absence)}</TableCell>
                          <TableCell className="text-[var(--color-ink)]">{a.cours?.nom ?? '—'}</TableCell>
                          <TableCell className="text-[var(--color-ink-dim)]">{a.motif ?? '—'}</TableCell>
                          <TableCell className="text-right">
                            <Badge tone={a.justifiee ? 'success' : 'danger'}>{a.justifiee ? 'Justifiée' : 'Non justifiée'}</Badge>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              ))}
          </div>
        )
      })}
    </div>
  )
}


