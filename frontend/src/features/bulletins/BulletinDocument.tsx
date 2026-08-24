import { appreciation } from '@/lib/bareme'
import { DocumentHeader, DocumentYearBox } from '@/components/print/DocumentHeader'
import { DocumentSignatures } from '@/components/print/DocumentSignatures'
import { DocumentFooter } from '@/components/print/DocumentFooter'
import type { Etablissement } from '@/features/etablissement/api'
import type { BulletinDetailFull } from './types'

export function BulletinDocument({
  detail,
  bareme,
  effectif,
  anneeLabel,
  etab,
}: {
  detail: BulletinDetailFull
  bareme: number
  effectif: number | null
  anneeLabel?: string
  etab?: Etablissement | null
}) {
  const estEf1 = bareme === 10
  const mention = detail.moyenne_generale != null ? appreciation(detail.moyenne_generale, bareme) : null

  return (
    <div className="print-doc">
      <DocumentHeader etab={etab} right={anneeLabel ? <DocumentYearBox label={anneeLabel} /> : undefined} />

      <div className="doc-title">Bulletin de notes</div>
      <div className="doc-title-sub">
        {detail.trimestre.nom} — {detail.classe.niveau} {detail.classe.nom}
      </div>

      <div className="doc-info-grid">
        <InfoCell label="Nom & Prénom" span={2} value={`${detail.eleve.nom} ${detail.eleve.prenom}`} />
        <InfoCell label="Matricule" value={detail.eleve.matricule} />
        <InfoCell label="Classe" value={`${detail.classe.niveau} ${detail.classe.nom}`} lastCol />
        <InfoCell label="Période" value={detail.trimestre.nom} lastRow />
        <InfoCell label="Effectif" value={effectif != null ? `${effectif} élève(s)` : '—'} lastRow />
        <InfoCell
          label="Rang"
          value={detail.rang != null ? `${detail.rang}${detail.rang === 1 ? 'er' : 'e'}${effectif ? ` / ${effectif}` : ''}` : '—'}
          lastRow
        />
        <InfoCell
          label="Moyenne générale"
          value={detail.moyenne_generale != null ? `${format2(detail.moyenne_generale)}/${bareme}` : '—'}
          lastRow
          lastCol
        />
      </div>

      <table className="doc-table">
        <thead>
          <tr>
            <th>Matière</th>
            <th className="num">Moyenne</th>
            {!estEf1 && (
              <>
                <th className="num">Coeff</th>
                <th className="num">Note × Coeff</th>
              </>
            )}
          </tr>
        </thead>
        <tbody>
          {detail.details.map((d) => (
            <tr key={d.id}>
              <td>{d.cours_nom}</td>
              <td className="num">{d.moyenne != null ? format2(d.moyenne) : '—'}</td>
              {!estEf1 && (
                <>
                  <td className="num">{d.coefficient}</td>
                  <td className="num">{d.moyenne != null ? format2(d.moyenne * d.coefficient) : '—'}</td>
                </>
              )}
            </tr>
          ))}
        </tbody>
        {!estEf1 && (
          <tfoot>
            <tr>
              <td>Totaux</td>
              <td />
              <td className="num">{sommeCoeff(detail)}</td>
              <td className="num">{format2(sommePoints(detail))}</td>
            </tr>
          </tfoot>
        )}
      </table>

      <div className="doc-summary">
        <SummaryItem label="Moyenne générale" value={detail.moyenne_generale != null ? `${format2(detail.moyenne_generale)}/${bareme}` : '—'} />
        <SummaryItem label="Mention" value={mention ?? '—'} />
        <SummaryItem label="Rang" value={detail.rang != null ? `${detail.rang}${detail.rang === 1 ? 'er' : 'e'}` : '—'} />
      </div>

      {detail.appreciation && (
        <div className="doc-appreciation">
          <div className="doc-appreciation-label">Appréciation du conseil de classe</div>
          <p className="doc-appreciation-text">{detail.appreciation}</p>
        </div>
      )}

      <DocumentFooter etab={etab} />

      <DocumentSignatures
        roles={['Le Chef d’Établissement', 'Le Professeur principal', 'Signature du Parent']}
      />
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

function SummaryItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="doc-summary-item">
      <div className="doc-summary-label">{label}</div>
      <div className="doc-summary-value">{value}</div>
    </div>
  )
}

function format2(n: number): string {
  return n.toFixed(2)
}

function sommeCoeff(detail: BulletinDetailFull): number {
  return detail.details.reduce((acc, d) => acc + d.coefficient, 0)
}

function sommePoints(detail: BulletinDetailFull): number {
  return detail.details.reduce((acc, d) => acc + (d.moyenne ?? 0) * d.coefficient, 0)
}
