export function DocumentSignatures({ roles }: { roles: string[] }) {
  return (
    <div className="doc-signatures">
      {roles.map((role) => (
        <div key={role} className="doc-signature">
          <div className="doc-signature-role">{role}</div>
          <div className="doc-signature-space" />
        </div>
      ))}
    </div>
  )
}
