import { DocumentHeader, DocumentYearBox } from '@/components/print/DocumentHeader'
import { DocumentSignatures } from '@/components/print/DocumentSignatures'
import { DocumentFooter } from '@/components/print/DocumentFooter'
import type { Etablissement } from '@/features/etablissement/api'
import type { RegistreNotes } from './api'

export function RegistreDocument({
  registre,
  anneeLabel,
  etab,
}: {
  registre: RegistreNotes
  anneeLabel?: string
  etab?: Etablissement | null
}) {
  const bareme = registre.bareme
  const trimestres = registre.trimestres

  return (
    <div className="print-doc">
      <DocumentHeader
        etab={etab}
        right={anneeLabel ? <DocumentYearBox label={anneeLabel} /> : undefined}
      />

      <div className="doc-title">Registre de notes</div>
      <div className="doc-title-sub">
        {registre.classe.niveau} {registre.classe.nom} — {registre.cours.nom} (coeff. {format2(registre.cours.coefficient)})
      </div>
      {registre.cours.enseignant && (
        <div className="doc-title-sub">
          Enseignant : {registre.cours.enseignant.prenom} {registre.cours.enseignant.nom}
        </div>
      )}

      <table className="doc-table doc-table-registre">
        <thead>
          <tr>
            <th>N°</th>
            <th>Nom & Prénom</th>
            {trimestres.map((t) => (
              <th key={t.id} colSpan={3} className="doc-cell-border">
                {t.nom}
              </th>
            ))}
            <th>Moy.</th>
          </tr>
          <tr>
            <th />
            <th />
            {trimestres.map((t) => (
              <GroupHeader key={t.id} bareme={bareme} />
            ))}
            <th className="num">{'Annuelle'}</th>
          </tr>
        </thead>
        <tbody>
          {registre.eleves.map((eleve, index) => (
            <tr key={eleve.matricule}>
              <td className="num">{index + 1}</td>
              <td>
                {eleve.prenom} {eleve.nom}
              </td>
              {trimestres.map((t) => {
                const ligne = eleve.lignes.find((l) => l.id_trimestre === t.id)
                return (
                  <GroupCell
                    key={t.id}
                    comp={ligne?.note_comp ?? null}
                    classe={ligne?.note_classe ?? null}
                    moyenne={ligne?.moyenne ?? null}
                  />
                )
              })}
              <td className="num">{eleve.moyenne_annuelle != null ? format2(eleve.moyenne_annuelle) : '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <DocumentFooter etab={etab} />

      <DocumentSignatures roles={['Le Directeur', 'La Secrétaire']} />
    </div>
  )
}

function GroupHeader({ bareme }: { bareme: number }) {
  return (
    <>
      <th className="num">Comp./{bareme}</th>
      <th className="num">Classe/{bareme}</th>
      <th className="num">{`Moy./${bareme}`}</th>
    </>
  )
}

function GroupCell({
  comp,
  classe,
  moyenne,
}: {
  comp: number | null
  classe: number | null
  moyenne: number | null
}) {
  return (
    <>
      <td className="num">{comp != null ? format2(comp) : '—'}</td>
      <td className="num">{classe != null ? format2(classe) : '—'}</td>
      <td className="num">{moyenne != null ? format2(moyenne) : '—'}</td>
    </>
  )
}

function format2(n: number): string {
  return n.toFixed(2)
}