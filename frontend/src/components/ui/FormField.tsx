import type { ReactNode } from 'react'

interface FormFieldProps {
  label: string
  required?: boolean
  error?: string
  hint?: string
  children: ReactNode
}

/** Design system §34 — FormField : label, contenu, erreur/hint, dans une colonne. */
export function FormField({ label, required, error, hint, children }: FormFieldProps) {
  return (
    <div className="flex flex-col gap-[5px]">
      <label className="text-[12px] font-medium text-[var(--ink-dim)]">
        {label}
        {required && <span className="ml-[2px] text-[var(--danger)]">*</span>}
      </label>
      {children}
      {error && <p className="text-[11.5px] text-[var(--danger)]">{error}</p>}
      {!error && hint && <p className="text-[11.5px] text-[var(--ink-faint)]">{hint}</p>}
    </div>
  )
}

/** Grille de formulaire 2 colonnes (§34 .form-grid-2). */
export function FormGrid2({ className, ...rest }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={clsxFn('grid grid-cols-1 gap-[14px] sm:grid-cols-2', className)} {...rest} />
}

function clsxFn(...parts: (string | undefined)[]) {
  return parts.filter(Boolean).join(' ')
}