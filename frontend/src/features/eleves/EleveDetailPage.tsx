import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useParams } from 'react-router-dom'
import { Pencil, Phone, MapPin, Briefcase, ChevronDown } from 'lucide-react'
import { useAuth } from '@/auth/useAuth'
import { Card, CardBody, CardHeader, CardTitle } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Avatar } from '@/components/ui/Avatar'
import { Spinner } from '@/components/ui/Spinner'
import { Tabs } from '@/components/ui/Tabs'
import { EmptyState } from '@/components/ui/EmptyState'
import { Button } from '@/components/ui/Button'
import { Table, TableBody, TableCell, TableContainer, TableHead, TableHeader, TableRow } from '@/components/ui/Table'
import { Breadcrumbs } from '@/components/ui/PageHeader'
import { formatDate, formatMontant, formatMoyenne } from '@/lib/format'
import { extractErrorMessage } from '@/lib/api'
import { baremeNiveau } from '@/lib/bareme'
import { toast } from '@/components/ui/toast'
import { fetchDossierEleve, updateEleve } from './api'
import { EleveFormDrawer } from './EleveFormDrawer'
import InscriptionFormDrawer from '@/features/inscriptions/InscriptionFormDrawer'
import { createInscription } from '@/features/inscriptions/api'
import { DocumentsTab } from '@/features/documents/DocumentsTab'
import { countVisibleDocuments, ELEVE_DOCS_LABELS } from '@/features/documents/labels'
import { uploadDocument } from '@/features/documents/api'
import type { DossierEleve, NoteEleve, InscriptionDetail, AbsenceEleve } from './types'

export default function EleveDetailPage() {
  const { matricule } = useParams<{ matricule: string }>()
  const { user } = useAuth()
  const canWrite = user?.role === 'admin' || user?.role === 'directeur'
  const canImportDocs = user?.role === 'admin'
  const [editOpen, setEditOpen] = useState(false)
  const [inscriptionOpen, setInscriptionOpen] = useState(false)

  const { data: dossier, isLoading, isError, refetch } = useQuery({
    queryKey: ['eleve-dossier', matricule],
    queryFn: () => fetchDossierEleve(matricule!),
    enabled: !!matricule,
  })

  const anneeMap = useMemo(() => {
    const map: Record<number, string> = {}
    for (const insc of dossier?.inscriptions ?? []) {
      if (insc.annee_scolaire) map[insc.annee_scolaire.id] = insc.annee_scolaire.libelle
    }
    if (dossier?.annee_scolaire && !(dossier.annee_scolaire.id in map)) {
      map[dossier.annee_scolaire.id] = dossier.annee_scolaire.libelle
    }
    return map
  }, [dossier])

  const anneeNiveau = useMemo(() => {
    const map: Record<number, string> = {}
    for (const insc of dossier?.inscriptions ?? []) {
      if (insc.annee_scolaire && insc.classe?.niveau) map[insc.annee_scolaire.id] = insc.classe.niveau
    }
    return map
  }, [dossier])

  const resultats = useMemo(
    () => regrouperResultats(dossier?.notes ?? [], anneeMap, anneeNiveau),
    [dossier, anneeMap, anneeNiveau],
  )
  const anneeActiveId = dossier?.annee_scolaire?.id
  // Un élève déjà inscrit (ou redoublant) pour l'année active n'a plus de
  // bouton « Inscrire » : l'inscription existe déjà.
  const dejaInscritAnneeActive = (dossier?.inscriptions ?? []).some(
    (i) => ['Inscrit', 'Redoublant'].includes(i.statut) && (anneeActiveId == null || i.id_annee_scolaire === anneeActiveId),
  )
  const nbAnneesAvecResultats = resultats.anneesTriees.length
  const anneeResultatsDefaut =
    anneeActiveId != null && resultats.parAnnee.has(anneeActiveId)
      ? anneeActiveId
      : (resultats.anneesTriees[0]?.id ?? null)

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
      <div className="flex justify-center py-24">
        <Spinner label="Chargement du dossier…" />
      </div>
    )
  }

  if (isError || !dossier) {
    return <EmptyState message="Impossible de charger ce dossier élève." />
  }

  return (
    <div className="w-full">
      <div className="flex flex-col gap-6">
      <Breadcrumbs
        items={[
          { label: 'Élèves', to: '/app/eleves' },
          { label: `${dossier.prenom} ${dossier.nom}` },
        ]}
      />

      <Card className="p-6">
        <div className="flex flex-col justify-between gap-5 sm:flex-row sm:items-start">
          <div className="flex items-start gap-4">
            <Avatar nom={dossier.nom} prenom={dossier.prenom} photo={dossier.photo} size="lg" highlighted />
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <h2 className="font-[var(--font-display)] text-2xl font-semibold tracking-tight text-[var(--color-ink)]">
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
            <div className="flex gap-2">
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
            label: 'Inscriptions',
            count: dossier.inscriptions.length,
            content: <InscriptionsTab inscriptions={dossier.inscriptions} />,
          },
          {
            key: 'notes',
            label: 'Résultats',
            count: nbAnneesAvecResultats,
            content: <NotesTab resultats={resultats} defaultExpandedId={anneeResultatsDefaut} />,
          },
          {
            key: 'absences',
            label: 'Absences',
            count: nbAbsencesActives,
            content: <AbsencesTab groups={absencesParAnnee} defaultExpandedId={anneeAbsencesDefaut} />,
          },
        
          {
            key: 'documents',
            label: 'Documents',
            count: countVisibleDocuments(dossier.documents, ELEVE_DOCS_LABELS),
            content: (
              <DocumentsTab
                documents={dossier.documents}
                labels={ELEVE_DOCS_LABELS}
                invalidateKey={['eleve-dossier', dossier.matricule]}
                upload={(typeDocument, file) => uploadDocument(dossier.matricule, typeDocument, file)}
                canEdit={canImportDocs}
              />
            ),
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
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
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
            <Briefcase strokeWidth={1.75} className="size-3.5 text-[var(--color-ink-faint)]" /> {dossier.tuteur.profession}
          </p>
          <p className="flex items-center gap-2 text-[var(--color-ink-dim)]">
            <Phone strokeWidth={1.75} className="size-3.5 text-[var(--color-ink-faint)]" /> {dossier.tuteur.telephone}
          </p>
          <p className="flex items-center gap-2 text-[var(--color-ink-dim)]">
            <MapPin strokeWidth={1.75} className="size-3.5 text-[var(--color-ink-faint)]" /> {dossier.tuteur.adresse}
          </p>
        </CardBody>
      </Card>

      <Card className="lg:col-span-2">
        <CardHeader>
          <CardTitle>Documents administratifs</CardTitle>
        </CardHeader>
        <CardBody className="grid gap-3 text-sm md:grid-cols-2">
          <div className="rounded-lg border border-[var(--color-border-soft)] px-3 py-2">
            <p className="text-[var(--color-ink-faint)]">Acte de naissance</p>
            <p className="mt-1 font-medium text-[var(--color-ink)]">{dossier.acte_naissance ? 'Présent' : 'À compléter'}</p>
          </div>
          <div className="rounded-lg border border-[var(--color-border-soft)] px-3 py-2">
            <p className="text-[var(--color-ink-faint)]">Carnet de santé</p>
            <p className="mt-1 font-medium text-[var(--color-ink)]">{dossier.carnet_sante ? 'Présent' : 'À compléter'}</p>
          </div>
          
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

interface PeriodeResultat {
  trimestre: NonNullable<NoteEleve['trimestre']>
  notes: NoteEleve[]
  estComplete: boolean
  moyennesParMatiere: {
    cours: NoteEleve['cours']
    moyenne: number
    nbNotes: number
    coefficient: number
    enseignant: NoteEleve['enseignant']
  }[]
}

function coefficientCours(cours: NoteEleve['cours'], idClasse: number): number {
  const aff = cours.coefficients.find((a) => a.id_classe === idClasse)
  return aff ? aff.coefficient : 1
}

// EF2 et au-delà : moyenne pondérée par coefficients.
// EF1 : moyenne arithmétique simple (notes /10, coefficients non applicables).
function moyennePeriode(moyennes: { moyenne: number; coefficient: number }[], ponderee: boolean): number | null {
  if (!ponderee) {
    return moyennes.length > 0 ? moyennes.reduce((somme, m) => somme + m.moyenne, 0) / moyennes.length : null
  }
  return moyennePonderee(moyennes)
}

function moyennePonderee(moyennes: { moyenne: number; coefficient: number }[]): number | null {
  let sommePonderee = 0
  let sommeCoefficients = 0
  for (const m of moyennes) {
    sommePonderee += m.moyenne * m.coefficient
    sommeCoefficients += m.coefficient
  }
  return sommeCoefficients > 0 ? sommePonderee / sommeCoefficients : null
}

interface AnneeResultat {
  id: number
  libelle: string
  bareme: number
  estPrimaire: boolean
  coursAttendus: { id: number; nom: string }[]
  periodes: PeriodeResultat[]
  moyenneAnnuelle: number | null
}

interface ResultatsEleve {
  parAnnee: Map<number, AnneeResultat>
  anneesTriees: AnneeResultat[]
}

function regrouperResultats(notes: NoteEleve[], anneeMap: Record<number, string>, anneeNiveau: Record<number, string>): ResultatsEleve {
  const parPeriode = new Map<number, PeriodeResultat>()
  for (const n of notes) {
    const trimestre = n.trimestre
    if (!trimestre) continue
    let periode = parPeriode.get(trimestre.id)
    if (!periode) {
      periode = { trimestre, notes: [], estComplete: false, moyennesParMatiere: [] }
      parPeriode.set(trimestre.id, periode)
    }
    periode.notes.push(n)
  }

  for (const periode of parPeriode.values()) {
    const byCours = new Map<number, { cours: NoteEleve['cours']; total: number; nbNotes: number; coefficient: number; enseignant: NoteEleve['enseignant'] }>()
    for (const n of periode.notes) {
      const cell = byCours.get(n.cours.id)
      if (cell) {
        cell.total += n.note
        cell.nbNotes += 1
        cell.enseignant = n.enseignant
      } else {
        byCours.set(n.cours.id, { cours: n.cours, total: n.note, nbNotes: 1, coefficient: coefficientCours(n.cours, n.id_classe), enseignant: n.enseignant })
      }
    }
    periode.moyennesParMatiere = [...byCours.values()]
      .map((cell) => ({ cours: cell.cours, moyenne: cell.total / cell.nbNotes, nbNotes: cell.nbNotes, coefficient: cell.coefficient, enseignant: cell.enseignant }))
      .sort((a, b) => a.cours.nom.localeCompare(b.cours.nom))
  }

  const parAnnee = new Map<number, AnneeResultat>()
  for (const periode of parPeriode.values()) {
    const aid = periode.trimestre.annee_scolaire_id
    let annee = parAnnee.get(aid)
    if (!annee) {
      const niveau = anneeNiveau[aid] ?? null
      const bareme = niveau ? baremeNiveau(niveau) : (periode.trimestre.type === 'COMPOSITION' ? 10 : 20)
      annee = {
        id: aid,
        libelle: anneeMap[aid] ?? `Année ${aid}`,
        bareme,
        estPrimaire: bareme === 10,
        coursAttendus: [],
        periodes: [],
        moyenneAnnuelle: null,
      }
      parAnnee.set(aid, annee)
    }
    annee.periodes.push(periode)
  }

  for (const annee of parAnnee.values()) {
    const coursById = new Map<number, { id: number; nom: string }>()
    for (const periode of annee.periodes) {
      for (const m of periode.moyennesParMatiere) {
        if (!coursById.has(m.cours.id)) coursById.set(m.cours.id, { id: m.cours.id, nom: m.cours.nom })
      }
    }
    annee.coursAttendus = [...coursById.values()].sort((a, b) => a.nom.localeCompare(b.nom))
    for (const periode of annee.periodes) {
      periode.estComplete =
        annee.coursAttendus.length > 0 && periode.moyennesParMatiere.length === annee.coursAttendus.length
    }
    annee.periodes.sort((a, b) => new Date(a.trimestre.date_debut).getTime() - new Date(b.trimestre.date_debut).getTime())

    const completes = annee.periodes.filter((p) => p.estComplete)
    annee.moyenneAnnuelle =
      completes.length > 0
        ? completes.reduce((somme, p) => {
            const moyenne = moyennePeriode(p.moyennesParMatiere, !annee.estPrimaire)
            return somme + (moyenne ?? 0)
          }, 0) / completes.length
        : null
  }

  const anneesTriees = [...parAnnee.values()].sort((a, b) => {
    const dernierA = Math.max(...a.periodes.map((p) => new Date(p.trimestre.date_debut).getTime()))
    const dernierB = Math.max(...b.periodes.map((p) => new Date(p.trimestre.date_debut).getTime()))
    return dernierB - dernierA
  })

  return { parAnnee, anneesTriees }
}

function NotesTab({ resultats, defaultExpandedId }: { resultats: ResultatsEleve; defaultExpandedId: number | null }) {
  const [expanded, setExpanded] = useState<Set<number>>(
    () => new Set(defaultExpandedId != null ? [defaultExpandedId] : []),
  )

  if (resultats.anneesTriees.length === 0) return <EmptyState message="Aucune matière et aucune note enregistrée." />

  const toggle = (id: number) =>
    setExpanded((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })

  return (
    <div className="flex flex-col gap-4">
      {resultats.anneesTriees.map((annee) => {
        const ouvert = expanded.has(annee.id)
        return (
          <div key={annee.id} className="flex flex-col gap-4">
            <button
              type="button"
              onClick={() => toggle(annee.id)}
              className="flex w-full items-center justify-between gap-3 rounded-[var(--radius-lg)] border border-[var(--color-border)] bg-[var(--color-surface-1)] px-4 py-3 text-left transition-colors hover:bg-[var(--color-surface-2)]"
            >
              <div className="flex flex-wrap items-center gap-2">
                <h4 className="font-medium text-[var(--color-ink)]">{annee.libelle}</h4>
                <Badge tone="neutral" className="text-xs">
                  {annee.periodes.length} période{annee.periodes.length > 1 ? 's' : ''}
                </Badge>
                {annee.moyenneAnnuelle != null && (
                  <span className="text-sm font-medium text-[var(--color-ink)]">
                    Moy. annuelle {annee.moyenneAnnuelle.toFixed(2)} /{annee.bareme}
                  </span>
                )}
              </div>
              <ChevronDown
                strokeWidth={1.75}
                className={`size-4 shrink-0 text-[var(--color-ink-faint)] transition-transform ${ouvert ? 'rotate-180' : ''}`}
              />
            </button>
            {ouvert && (
              <div className="flex flex-col gap-4">
                {annee.periodes.map((periode) => {
                  const avg = moyennePeriode(periode.moyennesParMatiere, !annee.estPrimaire)
                  return (
                    <Card key={periode.trimestre.id}>
                      <div className="flex items-center justify-between border-b border-[var(--color-border-soft)] px-5 py-3">
                        <div className="flex items-center gap-2">
                          <h4 className="font-medium text-[var(--color-ink)]">{periode.trimestre.nom}</h4>
                          <Badge tone={annee.estPrimaire ? 'warning' : 'info'} className="text-xs">
                            {annee.estPrimaire ? 'Composition' : 'Trimestre'}
                          </Badge>
                        </div>
                        <div className="flex items-center gap-4 text-sm">
                          {periode.estComplete ? (
                            <>
                              <span className="text-[var(--color-ink-dim)]">
                                {periode.moyennesParMatiere.length} matière{periode.moyennesParMatiere.length > 1 ? 's' : ''} notée{periode.moyennesParMatiere.length > 1 ? 's' : ''}
                              </span>
                              <span className="font-medium text-[var(--color-ink)]">Moy. {avg!.toFixed(2)} /{annee.bareme}</span>
                            </>
                          ) : (
                            <Badge tone="danger" className="text-xs">
                              Incomplète · {periode.moyennesParMatiere.length}/{annee.coursAttendus.length} matières
                            </Badge>
                          )}
                        </div>
                      </div>
                      <TableContainer className="rounded-none border-0">
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead>Matière</TableHead>
                              <TableHead>Enseignant</TableHead>
                              <TableHead className="text-right">Note /{annee.bareme}</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {annee.coursAttendus.map((cours) => {
                              const detail = periode.moyennesParMatiere.find((m) => m.cours.id === cours.id) ?? null
                              return (
                                <TableRow key={cours.id}>
                                  <TableCell className="text-[var(--color-ink)]">{cours.nom}</TableCell>
                                  <TableCell className="text-[var(--color-ink-dim)]">
                                    {detail ? `${detail.enseignant.prenom} ${detail.enseignant.nom}` : '—'}
                                  </TableCell>
                                  <TableCell className="text-right font-medium text-[var(--color-ink)]">
                                    {detail ? detail.moyenne.toFixed(2) : '—'}
                                  </TableCell>
                                </TableRow>
                              )
                            })}
                          </TableBody>
                        </Table>
                      </TableContainer>
                    </Card>
                  )
                })}
              </div>
            )}
          </div>
        )
      })}
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


