export function DocumentFooter({ etab }: { etab?: { adresse?: string | null; nom?: string } | null }) {
  const lieu = etab?.adresse?.split(',')[0]?.trim() || etab?.nom || null
  const date = new Date().toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' })

  return (
    <div className="doc-footer">
      <p style={{ textAlign: 'right' }}>
        {lieu ? `Fait à ${lieu}, le ` : 'Fait le '}
        {date}
      </p>
    </div>
  )
}
