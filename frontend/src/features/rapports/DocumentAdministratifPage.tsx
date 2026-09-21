import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Badge } from '@/components/ui/Badge'
import { Card, CardBody, CardHeader, CardTitle } from '@/components/ui/Card'
import { Select } from '@/components/ui/Select'
import { Tabs } from '@/components/ui/Tabs'
import { EmptyState } from '@/components/ui/EmptyState'
import { PageHeader } from '@/components/ui/PageHeader'
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/Table'
import { extractErrorMessage } from '@/lib/api'
import { estNiveauJardin } from '@/lib/niveaux'
import { fetchClasses } from '@/features/classes/api'
import {
  fetchPropositionPassage,
  fetchRapportRentree,
  fetchClassement,
  fetchFicheRenseignements,
  fetchFicheRenseignementsPremierCycle,
} from './api'
import type { ClasseProposition, ClassementClasse, FicheRenseignementsLigne, FicheRensPCLigne } from './types'

type Onglet = 'proposition' | 'rentree' | 'classement' | 'renseignements' | 'renseignements-premier-cycle'

const DOCUMENTS: Record<Onglet, { label: string; description: string }> = {
  proposition: {
    label: 'Proposition de passage',
    description:
      'Liste des élèves admis, recalés, en attente et exclus avec leur moyenne annuelle, pour l’année scolaire active.',
  },
  classement: {
    label: 'Classement des élèves',
    description:
      'Rang et moyenne annuelle des élèves pour l’année scolaire active, par classe et pour toutes les classes.',
  },
  renseignements: {
    label: 'Fiche de renseignements (2nd cycle)',
    description:
      'Effectifs par classe (7ème, 8ème, 9ème) et liste du personnel administratif et enseignant de l’établissement.',
  },
  'renseignements-premier-cycle': {
    label: 'Fiche de renseignements (1er cycle)',
    description:
      'Effectifs de la 1ère à la 6ème année, infrastructures et mobiliers, personnel de l’établissement.',
  },
  rentree: {
    label: 'Rapport succinct de rentrée',
    description:
      'Effectifs de rentrée par année d’études (garçons, filles, redoublants) pour l’année scolaire active.',
  },
}

function note(v: number | null): string {
  return v == null ? '—' : v.toFixed(2).replace('.', ',')
}

const LIBELLES_PROPOSITION: Record<string, { label: string; tone: 'success' | 'danger' | 'warning' | 'neutral' }> = {
  ADMIS: { label: 'Admis', tone: 'success' },
  RECALE: { label: 'Recalé(e)', tone: 'danger' },
  EN_ATTENTE: { label: 'En attente', tone: 'warning' },
  EXCLU: { label: 'Exclu', tone: 'danger' },
}

function statutBadge(statut: string | null) {
  if (!statut) return '—'
  const infos = LIBELLES_PROPOSITION[statut] ?? { label: statut, tone: 'neutral' as const }
  return <Badge tone={infos.tone}>{infos.label}</Badge>
}

function celluleColonnes(ligne: FicheRenseignementsLigne | FicheRensPCLigne) {
  if ('sept' in ligne) {
    return [
      { cle: '7ème', cell: ligne.sept },
      { cle: '8ème', cell: ligne.huit },
      { cle: '9ème', cell: ligne.neuf },
    ]
  }
  return ['1ère', '2ème', '3ème', '4ème', '5ème', '6ème'].map((cle, i) => ({
    cle,
    cell: (ligne as FicheRensPCLigne)[`annee_${i + 1}` as 'annee_1'],
  }))
}

export default function DocumentAdministratifPage() {
  const [onglet, setOnglet] = useState<Onglet>('proposition')
  const [classeId, setClasseId] = useState<number | null>(null)

  const { data: classes = [] } = useQuery({ queryKey: ['classes'], queryFn: fetchClasses })

  const selectedClasse = classes.find((c) => c.id === classeId) ?? null
  const jardinSelectionne = !!selectedClasse && estNiveauJardin(selectedClasse.niveau)

  const { data: proposition, isError: errProp } = useQuery({
    queryKey: ['rapport-proposition', classeId],
    queryFn: () => fetchPropositionPassage(classeId ? { classeId } : undefined),
    enabled: onglet === 'proposition' && !jardinSelectionne,
  })
  const { data: rentree, isError: errRentree } = useQuery({
    queryKey: ['rapport-rentree'],
    queryFn: () => fetchRapportRentree(),
    enabled: onglet === 'rentree',
  })
  const { data: classement, isError: errClassement } = useQuery({
    queryKey: ['rapport-classement', classeId],
    queryFn: () => fetchClassement(classeId ? { classeId } : undefined),
    enabled: onglet === 'classement',
  })
  const { data: renseignements, isError: errRenseignements } = useQuery({
    queryKey: ['rapport-renseignements'],
    queryFn: () => fetchFicheRenseignements(),
    enabled: onglet === 'renseignements',
  })
  const { data: renseignementsPc, isError: errRenseignementsPc } = useQuery({
    queryKey: ['rapport-renseignements-premier-cycle'],
    queryFn: () => fetchFicheRenseignementsPremierCycle(),
    enabled: onglet === 'renseignements-premier-cycle',
  })

  const aucuneClasse = classes.length === 0
  const estRentree = onglet === 'rentree'
  const estGlobal = estRentree || onglet === 'renseignements' || onglet === 'renseignements-premier-cycle'
  const actionsDisabled = estGlobal ? false : aucuneClasse || jardinSelectionne

  const messageErreur = (err: unknown) =>
    extractErrorMessage(err, 'Impossible de charger ce document.')

  const contenuDonnees = () => {
    if (actionsDisabled) {
      if (aucuneClasse) return <EmptyState message="Aucune classe enregistrée pour le moment." />
      return (
        <Card>
          <CardBody className="py-8">
            <EmptyState
              title="Pas de document au jardin"
              message="Ce document ne concerne que les classes du fondamental (1ère à 9ème Année)."
            />
          </CardBody>
        </Card>
      )
    }

    if (onglet === 'rentree') {
      if (errRentree) return <Message message={messageErreur(errRentree)} />
      if (!rentree) return null
      return <RapportRentreeData rapport={rentree} />
    }
    if (onglet === 'classement') {
      if (errClassement) return <Message message={messageErreur(errClassement)} />
      if (!classement) return null
      return <ClassementData classes={classement.classes} />
    }
    if (onglet === 'renseignements') {
      if (errRenseignements) return <Message message={messageErreur(errRenseignements)} />
      if (!renseignements) return null
      return <RenseignementsData fiche={renseignements} />
    }
    if (onglet === 'renseignements-premier-cycle') {
      if (errRenseignementsPc) return <Message message={messageErreur(errRenseignementsPc)} />
      if (!renseignementsPc) return null
      return <RenseignementsPremierCycleData fiche={renseignementsPc} />
    }
    if (errProp) return <Message message={messageErreur(errProp)} />
    if (!proposition) return null
    return <PropositionData classes={proposition.classes} />
  }

  const onglets = (Object.keys(DOCUMENTS) as Onglet[]).map((key) => ({
    key,
    label: DOCUMENTS[key].label,
  }))

  return (
    <div className="flex flex-col gap-5">
      <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
        <PageHeader
          title="Document administratif"
          subtitle={
            <p className="mt-1 text-sm text-[var(--ink-dim)]">
              Proposition de passage, classement des élèves, fiches de renseignements (1er et 2nd cycles) et
              rapport succinct de rentrée pour l'année scolaire active.
            </p>
          }
        />
        <div>
          <Select
            value={classeId ?? ''}
            onChange={(e) => setClasseId(e.target.value ? Number(e.target.value) : null)}
            options={[
              { value: '', label: 'Toutes les classes' },
              ...classes.map((c) => ({ value: c.id, label: `${c.niveau} — ${c.nom}` })),
            ]}
            className="w-56"
            disabled={classes.length === 0 || estGlobal}
          />
        </div>
      </div>

      <Tabs value={onglet} onChange={(k) => setOnglet(k as Onglet)} tabs={onglets} />

      {contenuDonnees()}
    </div>
  )
}

function Message({ message }: { message: string }) {
  return (
    <Card>
      <CardBody className="py-8">
        <EmptyState message={message} />
      </CardBody>
    </Card>
  )
}

function Ranges({ effectif, bareme }: { effectif?: number; bareme?: number }) {
  return (
    <div className="flex flex-wrap gap-2">
      {effectif != null && <Badge tone="neutral">Effectif : {effectif}</Badge>}
      {bareme != null && <Badge tone="neutral">Barème : {bareme}</Badge>}
    </div>
  )
}

/** Proposition de passage : synthèse par classe + tableau des élèves. */
function PropositionData({ classes }: { classes: ClasseProposition[] }) {
  if (classes.length === 0) {
    return <EmptyState message="Aucune donnée pour cette année scolaire." />
  }
  return (
    <div className="flex flex-col gap-4">
      {classes.map((c) => (
        <Card key={c.id_classe}>
          <CardHeader>
            <CardTitle>
              {c.niveau} — {c.nom}
            </CardTitle>
          </CardHeader>
          <CardBody className="flex flex-col gap-3">
            <Ranges effectif={c.effectif} bareme={c.bareme} />
            <div className="flex flex-wrap gap-2">
              <Badge tone="success">Admis : {c.admis}</Badge>
              <Badge tone="danger">Recalés : {c.recales}</Badge>
              <Badge tone="warning">En attente : {c.en_attente}</Badge>
              <Badge tone="danger">Exclus : {c.exclus}</Badge>
            </div>
            <TableElevesPropositions eleves={c.eleves} />
          </CardBody>
        </Card>
      ))}
    </div>
  )
}

function TableElevesPropositions({ eleves }: { eleves: ClasseProposition['eleves'] }) {
  return (
    <TableContainer>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Matricule</TableHead>
            <TableHead>Nom</TableHead>
            <TableHead>Prénom</TableHead>
            <TableHead>Sexe</TableHead>
            <TableHead>Date de Naissance</TableHead>
            <TableHead>Lieu de Naissance</TableHead>
            <TableHead>Prénom du Père</TableHead>
            <TableHead>Nom du Père</TableHead>
            <TableHead>Prénom de la Mère</TableHead>
            <TableHead>Nom de la Mère</TableHead>
            <TableHead>Année de Recrutement</TableHead>
            <TableHead className="text-center">Années dans la classe</TableHead>
            <TableHead className="text-right">Moyenne</TableHead>
            <TableHead>Proposition</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {eleves.map((e) => (
            <TableRow key={e.inscription_id}>
              <TableCell>{e.matricule}</TableCell>
              <TableCell>{e.nom}</TableCell>
              <TableCell>{e.prenom}</TableCell>
              <TableCell>{e.sexe ?? '—'}</TableCell>
              <TableCell>{e.date_naissance ?? '—'}</TableCell>
              <TableCell>{e.lieu_naissance ?? '—'}</TableCell>
              <TableCell>{e.prenom_pere ?? '—'}</TableCell>
              <TableCell>{e.nom_pere ?? '—'}</TableCell>
              <TableCell>{e.prenom_mere ?? '—'}</TableCell>
              <TableCell>{e.nom_mere ?? '—'}</TableCell>
              <TableCell>{e.annee_recrutement ?? '—'}</TableCell>
              <TableCell className="text-center">{e.annees_passees_classe}</TableCell>
              <TableCell className="text-right">{note(e.moyenne_annuelle)}</TableCell>
              <TableCell>{statutBadge(e.proposition)}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  )
}

/** Classement : rang + moyenne, par classe. */
function ClassementData({ classes }: { classes: ClassementClasse[] }) {
  if (classes.length === 0) {
    return <EmptyState message="Aucune donnée pour cette année scolaire." />
  }
  return (
    <div className="flex flex-col gap-4">
      {classes.map((c) => (
        <Card key={c.id_classe}>
          <CardHeader>
            <CardTitle>
              {c.niveau} — {c.nom}
            </CardTitle>
          </CardHeader>
          <CardBody className="flex flex-col gap-3">
            <Ranges effectif={c.effectif} bareme={c.bareme} />
            <TableContainer>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-14">Rang</TableHead>
                    <TableHead>Matricule</TableHead>
                    <TableHead>Nom</TableHead>
                    <TableHead>Prénom</TableHead>
                    <TableHead className="text-right">Moyenne</TableHead>
                    <TableHead>Observations</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {c.eleves.map((e) => (
                    <TableRow key={e.inscription_id}>
                      <TableCell>{e.rang ?? '—'}</TableCell>
                      <TableCell>{e.matricule}</TableCell>
                      <TableCell>{e.nom}</TableCell>
                      <TableCell>{e.prenom}</TableCell>
                      <TableCell className="text-right">{note(e.moyenne_annuelle)}</TableCell>
                      <TableCell>{statutBadge(e.observation)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </CardBody>
        </Card>
      ))}
    </div>
  )
}

function BlocEffectifs({ lignes }: { lignes: Array<FicheRenseignementsLigne | FicheRensPCLigne> }) {
  const colonnes = lignes.length > 0 ? celluleColonnes(lignes[0]) : []
  return (
    <TableContainer>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Libellé</TableHead>
            {colonnes.map((c) => (
              <TableHead key={c.cle} className="text-center">
                {c.cle}
              </TableHead>
            ))}
            <TableHead className="text-center">Total</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {lignes.map((ligne) => {
            const cols = celluleColonnes(ligne)
            const total = 'sept' in ligne ? ligne.total : ligne.total
            return (
              <TableRow key={ligne.libelle}>
                <TableCell className="font-medium">{ligne.libelle}</TableCell>
                {cols.map(({ cle, cell }) => (
                  <TableCell key={cle} className="text-center">
                    {cell.total}
                    <span className="block text-[var(--ink-faint)]">
                      {cell.garcons}G / {cell.filles}F
                    </span>
                  </TableCell>
                ))}
                <TableCell className="text-center">
                  {total.total}
                  <span className="block text-[var(--ink-faint)]">
                    {total.garcons}G / {total.filles}F
                  </span>
                </TableCell>
              </TableRow>
            )
          })}
        </TableBody>
      </Table>
    </TableContainer>
  )
}

function RenseignementsData({ fiche }: { fiche: import('./types').FicheRenseignementsResponse }) {
  return (
    <div className="flex flex-col gap-4">
      <Card>
        <CardHeader>
          <CardTitle>{fiche.ecole}</CardTitle>
        </CardHeader>
        <CardBody>
          <p className="text-sm text-[var(--ink-dim)]">
            Académie : {fiche.academie ?? '—'} · CAP : {fiche.cap ?? '—'} · Dirigée par :{' '}
            {fiche.dirigee_par ?? '—'} · Tél : {fiche.telephone ?? '—'}
          </p>
        </CardBody>
      </Card>
      <EnTeteTable titre="Effectifs par classe" />
      <BlocEffectifs lignes={fiche.effectifs} />
      {fiche.personnel.length > 0 && (
        <EnTeteTable titre="Personnel administratif et enseignant" />
      )}
      {fiche.personnel.length > 0 && (
        <TableContainer>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Prénom</TableHead>
                <TableHead>Nom</TableHead>
                <TableHead>Genre</TableHead>
                <TableHead>Catégorie</TableHead>
                <TableHead>Fonction</TableHead>
                <TableHead>Classe</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {fiche.personnel.map((p, i) => (
                <TableRow key={i}>
                  <TableCell>{p.prenom}</TableCell>
                  <TableCell>{p.nom}</TableCell>
                  <TableCell>{p.genre ?? '—'}</TableCell>
                  <TableCell>{p.categorie ?? '—'}</TableCell>
                  <TableCell>{p.fonction ?? '—'}</TableCell>
                  <TableCell>{p.classe ?? '—'}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </div>
  )
}

function RenseignementsPremierCycleData({ fiche }: { fiche: import('./types').FicheRenseignementsPremierCycleResponse }) {
  return (
    <div className="flex flex-col gap-4">
      <Card>
      <CardHeader>
        <CardTitle>{fiche.ecole}</CardTitle>
      </CardHeader>
      <CardBody>
        <p className="text-sm text-[var(--ink-dim)]">
          Village/Quartier : {fiche.village_quartier ?? '—'} · Commune : {fiche.commune ?? '—'} · CAP :{' '}
          {fiche.cap ?? '—'} · Dirigé par : {fiche.dirige_par ?? '—'} · Tél : {fiche.telephone ?? '—'}
        </p>
      </CardBody>
    </Card>
    <EnTeteTable titre="Effectifs par année" />
    <BlocEffectifs lignes={fiche.effectifs} />
      {fiche.personnel_admin.length > 0 && <EnTeteTable titre="Personnel administratif" />}
      {fiche.personnel_admin.length > 0 && (
        <TablePersonnel
          list={fiche.personnel_admin}
          colonnes={[
            { label: 'MLE', value: (p) => p.numero_mle },
            { label: 'Fonction', value: (p) => p.fonction },
            { label: 'Diplôme', value: (p) => p.diplome },
          ]}
        />
      )}
      {fiche.personnel_enseignant.length > 0 && <EnTeteTable titre="Personnel enseignant" />}
      {fiche.personnel_enseignant.length > 0 && (
        <TablePersonnel
          list={fiche.personnel_enseignant}
          colonnes={[
            { label: 'MLE', value: (p) => p.numero_mle },
            { label: 'Grade', value: (p) => p.grade },
            { label: 'Classe tenue', value: (p) => p.classe_tenue },
          ]}
        />
      )}
          {fiche.infrastructures && <BlocInfrastructuresMobiliers infra={fiche.infrastructures} />}
    </div>
  )
}

function BlocInfrastructuresMobiliers({ infra }: { infra: import('./types').FicheRensPCInfrastructures }) {
  const grille = [
    { t: 'Salles construites', p: [['en dur', infra.salles_dur], ['semi-dur', infra.salles_semi_dur], ['en banco', infra.salles_banco], ['autres', infra.salles_autres]] },
    { t: 'Directions', p: [['en dur', infra.direction_dur], ['en banco', infra.direction_banco], ['autres', infra.direction_autres], ['logement direction', infra.logement_direction]] },
    { t: 'Mobiliers', p: [['tables-bancs', infra.tables_bancs], ['chaises', infra.chaises], ['armoires', infra.armoires], ['tableaux', infra.tableaux], ['divers', infra.mobilier_divers]] },
  ]
  return (
    <>
      <EnTeteTable titre="Infrastructures et mobiliers" />
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        {grille.map((b) => (
          <div key={b.t} className="rounded-md border p-3">
            <p className="mb-2 font-medium">{b.t}</p>
            {b.p.map(([l, v]) => (
              <p key={l} className="flex justify-between text-sm">
                <span>{l}</span>
                <span>{v ?? '—'}</span>
              </p>
            ))}
          </div>
        ))}
      </div>
    </>
  )
}

function TablePersonnel({
  list,
  colonnes,
}: {
  list: import('./types').FicheRensPCPersonnel[]
  colonnes: { label: string; value: (p: import('./types').FicheRensPCPersonnel) => string | null }[]
}) {
  return (
    <TableContainer>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Prénom</TableHead>
            <TableHead>Nom</TableHead>
            {colonnes.map((c) => (
              <TableHead key={c.label}>{c.label}</TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {list.map((p, i) => (
            <TableRow key={i}>
              <TableCell>{p.prenom}</TableCell>
              <TableCell>{p.nom}</TableCell>
              {colonnes.map((c) => (
                <TableCell key={c.label}>{c.value(p) ?? '—'}</TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  )
}

function EnTeteTable({ titre }: { titre: string }) {
  return <p className="text-[10px] font-semibold uppercase tracking-[0.08em] text-[var(--ink-faint)]">{titre}</p>
}

/** Rapport succinct de rentrée : résumé + effectifs par année + cycles. */
function RapportRentreeData({ rapport }: { rapport: import('./types').RapportRentree }) {
  return (
    <div className="flex flex-col gap-4">
      <Card>
        <CardHeader>
          <CardTitle>{rapport.ecole}</CardTitle>
        </CardHeader>
        <CardBody className="flex flex-col gap-3">
          <p className="text-sm text-[var(--ink-dim)]">
            Village/Quartier : {rapport.village_quartier ?? '—'} · Commune : {rapport.commune ?? '—'} · CAP :{' '}
            {rapport.cap ?? '—'} · Cercle : {rapport.cercle ?? '—'} · AE : {rapport.ae ?? '—'}
          </p>
          <div className="flex flex-wrap gap-2">
            <Badge tone="neutral">Garçons : {rapport.total_garcons}</Badge>
            <Badge tone="neutral">Filles : {rapport.total_filles}</Badge>
            <Badge tone="neutral">Total : {rapport.total_general}</Badge>
            <Badge tone="warning">Redoublants : {rapport.total_redoublants}</Badge>
          </div>
        </CardBody>
      </Card>
      <EnTeteTable titre="Effectifs par année d'études" />
      <TableContainer>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Année</TableHead>
              <TableHead className="text-center">Groupes</TableHead>
              <TableHead className="text-center">Garçons</TableHead>
              <TableHead className="text-center">Filles</TableHead>
              <TableHead className="text-center">Total</TableHead>
              <TableHead className="text-center">Redoublants</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rapport.classes.map((c, i) => (
              <TableRow key={i}>
                <TableCell>{c.annee_etude}</TableCell>
                <TableCell className="text-center">{c.groupes}</TableCell>
                <TableCell className="text-center">{c.garcons}</TableCell>
                <TableCell className="text-center">{c.filles}</TableCell>
                <TableCell className="text-center">{c.total}</TableCell>
                <TableCell className="text-center">
                  {c.redoublants_g}G / {c.redoublants_f}F
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
      <EnTeteTable titre="Cycles" />
      <TableContainer>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Cycle</TableHead>
              <TableHead className="text-center">FE</TableHead>
              <TableHead className="text-center">FC</TableHead>
              <TableHead className="text-center">CE</TableHead>
              <TableHead className="text-center">CC</TableHead>
              <TableHead className="text-center">Autres</TableHead>
              <TableHead className="text-center">EM</TableHead>
              <TableHead className="text-center">Total</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {[rapport.premiers_cycle, rapport.second_cycle].map((c, i) => (
              <TableRow key={i}>
                <TableCell>{c.cycle}</TableCell>
                <TableCell className="text-center">{c.fe}</TableCell>
                <TableCell className="text-center">{c.fc}</TableCell>
                <TableCell className="text-center">{c.ce}</TableCell>
                <TableCell className="text-center">{c.cc}</TableCell>
                <TableCell className="text-center">{c.autres}</TableCell>
                <TableCell className="text-center">{c.em}</TableCell>
                <TableCell className="text-center">{c.total}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </div>
  )
}