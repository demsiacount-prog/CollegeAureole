import { urlAbsolue } from '@/lib/server'
import type { Etablissement } from '@/features/etablissement/api'

export function DocumentHeader({
  etab,
  right,
}: {
  etab?: Etablissement | null
  right?: React.ReactNode
}) {
  const nom = etab?.nom ?? 'Établissement scolaire'
  const contact = [etab?.adresse, etab?.telephone, etab?.email].filter(Boolean).join(' · ')

  return (
    <div className="doc-letterhead">
      {etab?.logo ? <img src={urlAbsolue(etab.logo)} alt={`Logo de ${nom}`} /> : null}
      <div className="doc-school-block">
        <div className="doc-school-name">{nom}</div>
        {(etab?.sigle || etab?.devise) && (
          <div className="doc-school-sub">
            {[etab?.sigle, etab?.devise].filter(Boolean).join(' — ')}
          </div>
        )}
        {contact && <div className="doc-school-contact">{contact}</div>}
      </div>
      {right ? <div>{right}</div> : null}
    </div>
  )
}

export function DocumentYearBox({ label }: { label: string }) {
  return (
    <div className="doc-year-box">
      Année Scolaire
      <br />
      {label}
    </div>
  )
}
