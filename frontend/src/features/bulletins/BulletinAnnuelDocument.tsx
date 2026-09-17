import { DocumentHeader, DocumentYearBox } from '@/components/print/DocumentHeader'
import { DocumentSignatures } from '@/components/print/DocumentSignatures'
import { DocumentFooter } from '@/components/print/DocumentFooter'
import type { Etablissement } from '@/features/etablissement/api'
import type { BulletinAnnuel } from './types'

export function BulletinAnnuelDocument({
  annuel,
  anneeLabel,
  etab,
}: {
  annuel: BulletinAnnuel
  anneeLabel?: string
  etab?: Etablissement | null
}) {
  const bareme = annuel.bareme

  return (
    <div className="print-doc">
      <DocumentHeader
        etab={etab}
        right={anneeLabel ? <DocumentYearBox label={anneeLabel} /> : undefined}
      />

      <div className="doc-title">Bulletin de notes annuel</div>
      <div className="doc-title-sub">
        {annuel.classe.niveau} {annuel.classe.nom}
      </div>

      <div className="doc-info-grid">
        <InfoCell label="Nom & Prénom" span={2} value={`${annuel.eleve.nom} ${annuel.eleve.prenom}`} />
        <InfoCell label="Matricule" value={annuel.eleve.matricule} />
        <InfoCell label="Classe" value={`${annuel.classe.niveau} ${annuel.classe.nom}`} lastCol />
        <InfoCell label="Année scolaire" value={anneeLabel ?? annuel.annee_libelle ?? '—'} lastRow />
        <InfoCell
          label="Moyenne annuelle"
          value={annuel.moyenne_annuelle != null ? `${format2(annuel.moyenne_annuelle)}/${bareme}` : '—'}
          lastRow
        />
        <InfoCell label="Rang annuel" value={annuel.rang_annuel != null ? format2(annuel.rang_annuel) : '—'} lastRow />
        <InfoCell label="Mention" value={annuel.mention_annuelle ?? '—'} lastRow lastCol />
      </div>

      {annuel.trimestres.map((bloc) => (
        <div key={bloc.id_trimestre}>
          <div className="doc-bloc-title">— {bloc.nom} —</div>

          <table className="doc-table">
            <thead>
              <tr>
                <th>Matière</th>
                <th className="num">Coeff</th>
                <th className="num">Note Classe</th>
                <th className="num">Note Comp.</th>
                <th className="num">Moyenne</th>
                <th className="num">Moy. Coeff.</th>
                <th>Appréciation</th>
              </tr>
            </thead>
            <tbody>
              {bloc.lignes.map((l) => (
                <tr key={l.id_cours}>
                  <td>{l.cours_nom}</td>
                  <td className="num">{format2(l.coefficient)}</td>
                  <td className="num">{l.note_classe != null ? format2(l.note_classe) : '—'}</td>
                  <td className="num">{l.note_comp != null ? format2(l.note_comp) : '—'}</td>
                  <td className="num">{l.moyenne != null ? format2(l.moyenne) : '—'}</td>
                  <td className="num">{l.points != null ? format2(l.points) : '—'}</td>
                  <td>{l.appreciation ?? '—'}</td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr>
                <td>Totaux</td>
                <td className="num">{format2(bloc.totaux_coefficients)}</td>
                <td colSpan={4} className="num">{format2(bloc.totaux_points)}</td>
                <td />
              </tr>
            </tfoot>
          </table>

          <div className="doc-bloc-recap">
            Moyenne : {bloc.moyenne_generale != null ? `${format2(bloc.moyenne_generale)}/${bloc.bareme}` : '—'} — Rang :{' '}
            {bloc.rang != null ? `${bloc.rang}/${bloc.effectif ?? '—'}` : '—'} — Moyenne du 1er élève :{' '}
            {bloc.moyenne_premier != null ? `${format2(bloc.moyenne_premier)}/${bloc.bareme}` : '—'}
          </div>
        </div>
      ))}

      <div className="doc-appreciation">
        <div className="doc-appreciation-label">Décision du conseil des maîtres</div>
        <p className="doc-appreciation-text">{annuel.decision ?? '—'}</p>
      </div>

      <DocumentFooter etab={etab} />

      <DocumentSignatures roles={['Le Directeur', 'Signature du Parent']} />
    </div>
  )
}

function InfoCell({
  label,
  value,
  span = 1,
  lastCol = false,
  lastRow = false,
}: {
  label: string
  value: string
  span?: number
  lastCol?: boolean
  lastRow?: boolean
}) {
  const classes = ['doc-info-cell']
  if (lastCol) classes.push('last-col')
  if (lastRow) classes.push('last-row')
  return (
    <div className={classes.join(' ')} style={span > 1 ? { gridColumn: `span ${span}` } : undefined}>
      <div className="doc-info-label">{label}</div>
      <div className="doc-info-value">{value || '—'}</div>
    </div>
  )
}

function format2(n: number): string {
  return n.toFixed(2)
}