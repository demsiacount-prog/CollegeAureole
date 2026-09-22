import { useQuery } from '@tanstack/react-query'
import axios from 'axios'
import { Badge } from '@/components/ui/Badge'
import { Card } from '@/components/ui/Card'
import { EmptyState } from '@/components/ui/EmptyState'
import { Spinner } from '@/components/ui/Spinner'
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
import { formatDate } from '@/lib/format'
import { fetchFicheSuivi } from './api'
import type { FicheSuivi } from './types'

const LIBELLES_STATUT: Record<string, string> = {
  ADMIS: 'Admis',
  RECALE: 'Recalé(e)',
  EN_ATTENTE: 'En attente',
  EXCLU: 'Exclu',
}

function note(v: number | null): string {
  return v == null ? '—' : v.toFixed(2).replace('.', ',')
}

function statutBadge(statut: string | null) {
  if (!statut) return '—'
  const tone =
    statut === 'ADMIS' ? 'success' : statut === 'RECALE' ? 'danger' : statut === 'EN_ATTENTE' ? 'warning' : 'neutral'
  return <Badge tone={tone}>{LIBELLES_STATUT[statut] ?? statut}</Badge>
}

export function FicheSuiviSection({ matricule }: { matricule: string }) {
  const { data: fiche, isLoading, isError, error } = useQuery({
    queryKey: ['fiche-suivi', matricule],
    queryFn: () => fetchFicheSuivi(matricule),
  })

  if (isLoading) {
    return (
      <Card className="mb-4 w-full p-4">
        <div className="flex justify-center py-3">
          <Spinner label="Chargement de la fiche de suivi…" />
        </div>
      </Card>
    )
  }

  if (isError || !fiche) {
    // Un élève de 7ème-9ème sans inscription active dans l'année consultée n'a
    // pas de classe (niveau nul) : le backend renvoie 403 pour signaler que la
    // fiche de suivi ne s'applique pas. On présente un état vide explicite plutôt
    // qu'une erreur brute.
    const estSansInscription = axios.isAxiosError(error) && error.response?.status === 403
    return (
      <Card className="mb-4 w-full p-4">
        {estSansInscription ? (
          <EmptyState
            title="Fiche de suivi indisponible"
            message="Cet élève n'a pas d'inscription active dans l'année consultée. La fiche de suivi s'adresse aux élèves du second cycle (7ème, 8ème et 9ème année) ; vérifiez son inscription."
          />
        ) : (
          <p className="text-sm text-[var(--ink-dim)]">
            {extractErrorMessage(error, 'Impossible de charger la fiche de suivi.')}
          </p>
        )}
      </Card>
    )
  }

  return <ContenuFiche fiche={fiche} />
}

function ContenuFiche({ fiche }: { fiche: FicheSuivi }) {
  const sousComptes = fiche.colonnes.map((c) => Math.max(1, c.moyennes.length))

  return (
    <Card className="mb-4 w-full p-4">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <p className="text-sm font-medium text-[var(--ink)]">Fiche de suivi et de transfert</p>
        {fiche.orientation && <Badge tone="info">Orientation : {fiche.orientation}</Badge>}
      </div>

      <div className="mb-4 grid grid-cols-1 gap-1.5 rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-2)] px-3 py-2.5 sm:grid-cols-2 lg:grid-cols-3">
        <p className="text-[11.5px] text-[var(--ink)]">
          <span className="text-[var(--ink-faint)]">Élève : </span>
          {fiche.nom} {fiche.prenom}
        </p>
        <p className="text-[11.5px] text-[var(--ink)]">
          <span className="text-[var(--ink-faint)]">Classe : </span>
          {fiche.classe ?? '—'}
        </p>
        <p className="text-[11.5px] text-[var(--ink)]">
          <span className="text-[var(--ink-faint)]">Année : </span>
          {fiche.annee_label}
        </p>
        <p className="text-[11.5px] text-[var(--ink)]">
          <span className="text-[var(--ink-faint)]">Naissance : </span>
          {fiche.date_de_naissance ? formatDate(fiche.date_de_naissance) : '—'} · {fiche.lieu_de_naissance}
        </p>
        <p className="text-[11.5px] text-[var(--ink)]">
          <span className="text-[var(--ink-faint)]">Sexe : </span>
          {fiche.sexe}
        </p>
        <p className="text-[11.5px] text-[var(--ink)]">
          <span className="text-[var(--ink-faint)]">Adresse : </span>
          {fiche.adresse ?? '—'}
        </p>
        <p className="text-[11.5px] text-[var(--ink)]">
          <span className="text-[var(--ink-faint)]">Père : </span>
          {fiche.pere ?? '—'}
        </p>
        <p className="text-[11.5px] text-[var(--ink)]">
          <span className="text-[var(--ink-faint)]">Mère : </span>
          {fiche.mere ?? '—'}
        </p>
        <p className="text-[11.5px] text-[var(--ink)]">
          <span className="text-[var(--ink-faint)]">Absences : </span>
          {fiche.nb_absences} (dont {fiche.nb_absences_injustifiees} injustifiées)
        </p>
      </div>

      <div className="mb-4 flex flex-wrap gap-2">
        <Badge tone="neutral">Moyenne annuelle : {note(fiche.moyenne_annuelle)}</Badge>
        {fiche.rang != null && (
          <Badge tone="neutral">
            Rang : {fiche.rang}/{fiche.effectif ?? '—'}
          </Badge>
        )}
        {fiche.transfert && <Badge tone="info">Année de transfert</Badge>}
      </div>

      {fiche.moyennes_trimestres.length > 0 && (
        <div className="mb-4">
          <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.08em] text-[var(--ink-faint)]">
            Moyennes par trimestre
          </p>
          <TableContainer>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Période</TableHead>
                  <TableHead>Moyenne</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {fiche.moyennes_trimestres.map((m) => (
                  <TableRow key={m.periode}>
                    <TableCell>{m.periode}</TableCell>
                    <TableCell>{note(m.moyenne)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </div>
      )}

      {fiche.notes_par_matiere.length > 0 && (
        <div className="mb-4">
          <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.08em] text-[var(--ink-faint)]">
            Notes par matière
          </p>
          <TableContainer>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Matière</TableHead>
                  <TableHead className="text-right">Notes</TableHead>
                  <TableHead className="text-right">Moyenne</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {fiche.notes_par_matiere.map((n) => (
                  <TableRow key={n.matiere}>
                    <TableCell>{n.matiere}</TableCell>
                    <TableCell className="text-right">{n.nb_notes}</TableCell>
                    <TableCell className="text-right">{note(n.moyenne)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </div>
      )}

      <div className="mb-4">
        <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.08em] text-[var(--ink-faint)]">
          Grille de suivi sur le cycle
        </p>
        <TableContainer>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Matière</TableHead>
                {fiche.colonnes.map((c) => (
                  <TableHead key={c.label} colSpan={Math.max(1, c.moyennes.length)} className="text-center">
                    {c.label}
                  </TableHead>
                ))}
                <TableHead className="text-center">Tendance</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {fiche.lignes.map((ligne) => {
                let offset = 0
                return (
                  <TableRow key={ligne.matiere}>
                    <TableCell className="font-medium">{ligne.matiere}</TableCell>
                    {sousComptes.map((nb, i) => {
                      const cellules = ligne.valeurs.slice(offset, offset + nb)
                      offset += nb
                      return (
                        <TableCell key={i} className="text-center">
                          {cellules.map((v, j) => (
                            <span key={j} className="mx-0.5">
                              {note(v)}
                            </span>
                          ))}
                        </TableCell>
                      )
                    })}
                    <TableCell className="text-center">{ligne.tendance ?? '—'}</TableCell>
                  </TableRow>
                )
              })}
            </TableBody>
          </Table>
        </TableContainer>
      </div>

      <div className="mb-4">
        <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.08em] text-[var(--ink-faint)]">
          Bilan des passages
        </p>
        <TableContainer>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Période</TableHead>
                <TableHead>Année scolaire</TableHead>
                <TableHead className="text-right">Moyenne annuelle</TableHead>
                <TableHead>Statut</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {fiche.colonnes.map((c) => (
                <TableRow key={c.label}>
                  <TableCell>{c.label}</TableCell>
                  <TableCell>{c.annee_label ?? '—'}</TableCell>
                  <TableCell className="text-right">
                    {c.effectue ? note(c.moyenne_annuelle) : '—'}
                  </TableCell>
                  <TableCell>{statutBadge(c.statut_passage)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </div>

      {fiche.parcours.length > 0 && (
        <div className="mb-4">
          <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.08em] text-[var(--ink-faint)]">
            Parcours scolaire
          </p>
          <TableContainer>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Année</TableHead>
                  <TableHead>Classe</TableHead>
                  <TableHead className="text-right">Moyenne</TableHead>
                  <TableHead>Statut</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {fiche.parcours.map((p, i) => (
                  <TableRow key={`${p.annee_label}-${i}`}>
                    <TableCell>{p.annee_label}</TableCell>
                    <TableCell>{p.classe ?? '—'}</TableCell>
                    <TableCell className="text-right">{note(p.moyenne_annuelle)}</TableCell>
                    <TableCell>{statutBadge(p.statut_passage)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </div>
      )}

      {fiche.remarques.length > 0 && (
        <div>
          <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.08em] text-[var(--ink-faint)]">
            Remarques
          </p>
          <ul className="list-inside list-disc space-y-1 text-[12px] text-[var(--ink-dim)]">
            {fiche.remarques.map((r) => (
              <li key={r}>{r}</li>
            ))}
          </ul>
        </div>
      )}
    </Card>
  )
}