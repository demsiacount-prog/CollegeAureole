import { Fragment } from 'react'
import { urlAbsolue } from '@/lib/server'
import type { Etablissement } from '@/features/etablissement/api'
import type { BulletinAnnuel } from './types'

const LIBELLES_TR = ['1er Trimestre', '2e Trimestre', '3e Trimestre']
const SOUS_ENTETES = ['Coéf', 'Note', 'Note', 'Moy.', 'Moy.', 'Appréc.']
const SOUS_ENTETES_2 = ['', 'Classe', 'Comp.', '', 'Coéf.', 'du Maître']
const LARGEURS_SOUS = ['4.8mm', '5.8mm', '5.8mm', '5.8mm', '6.9mm', '12.2mm']

function fmt2(n: number | null | undefined): string {
  return n != null ? n.toFixed(2) : ''
}

function fmtCoef(c: number | null | undefined): string {
  if (c == null) return ''
  return Number.isInteger(c) ? String(c) : c.toFixed(2)
}

export function BulletinNoteDocument({
  annuel,
  anneeLabel,
  etab,
}: {
  annuel: BulletinAnnuel
  anneeLabel?: string
  etab?: Etablissement | null
}) {
  const trimestres = annuel.trimestres
  const bareme = annuel.bareme
  const lignes = trimestres[0]?.lignes ?? []
  const nbTrim = Math.max(1, Math.min(trimestres.length, 3))
  const vides = Math.max(0, 3 - nbTrim)

  if (!trimestres.length || lignes.length === 0) {
    return (
      <div className="print-doc doc-bulletin">
        <p className="bn-academie">Bulletin de note indisponible</p>
        <p className="bn-adr">Aucun trimestre renseigné pour cet élève.</p>
      </div>
    )
  }

  const meilleur1er = trimestres.reduce<number | null>((acc, t) => {
    if (t.moyenne_premier == null) return acc
    return acc == null || t.moyenne_premier > acc ? t.moyenne_premier : acc
  }, null)

  const moyenne = fmt2(annuel.moyenne_annuelle)
  const rang = annuel.rang_annuel != null ? String(annuel.rang_annuel) : '——'
  const decision = annuel.decision ?? ''
  const classe = [annuel.classe.niveau, annuel.classe.nom].filter(Boolean).join(' ')
  const nomEcole = (etab?.nom ?? 'COLLÈGE AUREOLE').toUpperCase()

  return (
    <div className="print-doc doc-bulletin">
      <header className="bn-entete">
        <div className="bn-gauche">
          <p className="bn-academie">{etab?.academie ?? 'Académie de Kalaban Coro'}</p>
          <p className="bn-cap">{etab?.cap ?? 'CAP de Kalaban Coro'}</p>
          <div className="bn-cercle">
            {etab?.logo ? (
              <img className="bn-cercle-img" src={urlAbsolue(etab.logo)} alt={nomEcole} />
            ) : (
              nomEcole
            )}
          </div>
          {etab?.adresse ? <p className="bn-adr">{etab.adresse}</p> : null}
          {etab?.telephone ? <p className="bn-adr">Tél : {etab.telephone}</p> : null}
        </div>

        <div className="bn-centre">
          <p>
            Moyenne annuelle : <span className="bn-souligne">{moyenne || '——'}</span>
          </p>
          <p>
            Rang annuel : <span className="bn-souligne">{rang}</span>
          </p>
          <p>
            Décision du conseil des maîtres : <span className="bn-souligne">{decision || '——'}</span>
          </p>
        </div>

        <div className="bn-droite">
          <p>
            Année scolaire : <span className="bn-souligne">{anneeLabel ?? annuel.annee_libelle ?? ''}</span>
          </p>
          <p>
            Prénom : <span className="bn-souligne">{annuel.eleve.prenom}</span>
          </p>
          <p>
            Nom : <span className="bn-souligne">{annuel.eleve.nom}</span>
          </p>
          <p>
            Classe : <span className="bn-souligne">{classe}</span>
          </p>
        </div>
      </header>

      <h1 className="bn-titre">BULLETIN DE NOTE</h1>

      <table className="bn-table">
        <colgroup>
          <col style={{ width: '20.6mm' }} />
          {Array.from({ length: nbTrim }).flatMap(() =>
            LARGEURS_SOUS.map((w, k) => <col key={`${k}-${w}`} style={{ width: w }} />),
          )}
        </colgroup>
        <thead>
          <tr>
            <th rowSpan={2} className="bn-matiere bn-tr-head">
              Matières
            </th>
            {trimestres.slice(0, 3).map((t, i) => (
              <th key={t.id_trimestre} colSpan={6} className="bn-tr-head">
                {t.nom || LIBELLES_TR[i]}
              </th>
            ))}
            {Array.from({ length: vides }).map((_, k) => (
              <th key={`vide-${k}`} colSpan={6} className="bn-tr-head" />
            ))}
          </tr>
          <tr>
            {Array.from({ length: nbTrim }).flatMap((_, k) =>
              SOUS_ENTETES.map((h, j) => (
                <th key={`s-${k}-${j}`} className="bn-sub-head">
                  {h}
                  {SOUS_ENTETES_2[j] && <br />}
                  {SOUS_ENTETES_2[j]}
                </th>
              )),
            )}
          </tr>
        </thead>
        <tbody>
          {lignes.map((ligne, i) => (
            <tr key={ligne.id_cours}>
              <td className={`bn-matiere${ligne.cours_nom === 'Informatique' ? ' bn-matiere-ital' : ''}`}>
                {ligne.cours_nom}
              </td>
              {trimestres.slice(0, 3).map((t, k) => {
                const l = t.lignes[i]
                if (!l) {
                  return <td key={`m-${k}`} colSpan={6} />
                }
                return (
                  <Fragment key={k}>
                    <td className="bn-num">{fmtCoef(l.coefficient)}</td>
                    <td className="bn-num">{l.note_classe != null ? fmt2(l.note_classe) : ''}</td>
                    <td className="bn-num">{l.note_comp != null ? fmt2(l.note_comp) : ''}</td>
                    <td className="bn-num">{l.moyenne != null ? fmt2(l.moyenne) : ''}</td>
                    <td className="bn-num">{l.points != null ? fmt2(l.points) : ''}</td>
                    <td>{l.appreciation ?? ''}</td>
                  </Fragment>
                )
              })}
              {Array.from({ length: vides }).map((_, k) => (
                <td key={`mv-${k}`} colSpan={6} />
              ))}
            </tr>
          ))}
        </tbody>
        <tfoot>
          <tr className="bn-total">
            <td className="bn-matiere">Totaux</td>
            {trimestres.slice(0, 3).map((t, k) => (
              <Fragment key={k}>
                <td className="bn-num">{fmt2(t.totaux_coefficients)}</td>
                <td colSpan={4} />
                <td className="bn-num">{fmt2(t.totaux_points)}</td>
              </Fragment>
            ))}
            {Array.from({ length: vides }).map((_, k) => (
              <td key={`tv-${k}`} colSpan={6} />
            ))}
          </tr>
        </tfoot>
      </table>

      <div className="bn-footer-wrapper">
        <div className="bn-footer-spacer" />
        <div className="bn-footer">
          <div className="bn-footer-col">
            <p>
              Moyenne : <span className="bn-souligne">{moyenne || '——'} / {bareme}</span>
            </p>
          </div>
          <div className="bn-footer-col">
            <p>
              Moyenne du 1er : <span className="bn-souligne">{meilleur1er != null ? fmt2(meilleur1er) : '——'} / {bareme}</span>
            </p>
          </div>
          <div className="bn-footer-col">
            <p>Appréciation du Directeur :</p>
            <div className="bn-ligne" />
            <div className="bn-ligne" />
            <div className="bn-ligne" />
            <p className="bn-parent">Le Parent</p>
          </div>
        </div>
      </div>
    </div>
  )
}