export type Errors = Partial<Record<string, string>>

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

export const required = (value: unknown, label = 'Ce champ'): string | undefined =>
  value == null || String(value).trim() === '' ? `${label} est obligatoire.` : undefined

export const minNumber = (value: unknown, min: number, label = 'Ce champ'): string | undefined => {
  const n = typeof value === 'number' ? value : Number(value)
  if (value === '' || value == null) return `${label} est obligatoire.`
  if (!Number.isFinite(n)) return `${label} doit être un nombre.`
  return n >= min ? undefined : `${label} doit être au moins ${min}.`
}

export const positiveNumber = (value: unknown, label = 'Ce champ'): string | undefined => {
  const n = typeof value === 'number' ? value : Number(value)
  if (value === '' || value == null) return `${label} est obligatoire.`
  if (!Number.isFinite(n)) return `${label} doit être un nombre.`
  return n > 0 ? undefined : `${label} doit être un nombre positif.`
}

export const email = (value: unknown): string | undefined => {
  const v = String(value ?? '').trim()
  if (v === '') return undefined
  return EMAIL_RE.test(v) ? undefined : "L'e-mail n'est pas valide."
}

export const phone = (value: unknown): string | undefined => {
  const v = String(value ?? '').trim()
  if (v === '') return undefined
  const digits = v.replace(/\D/g, '')
  return digits.length >= 8 ? undefined : 'Le numéro de téléphone est invalide.'
}

export const dateFinApresDebut = (debut: string, fin: string): string | undefined =>
  debut && fin && fin < debut ? 'La date de fin doit être après la date de début.' : undefined

export const heureFinApresDebut = (debut: string, fin: string): string | undefined =>
  debut && fin && fin <= debut ? "L'heure de fin doit être après l'heure de début." : undefined

export const minLength = (value: unknown, min: number, label = 'Ce champ'): string | undefined => {
  const v = String(value ?? '')
  return v.length >= min ? undefined : `${label} doit contenir au moins ${min} caractères.`
}

export function validateFields(rules: Record<string, string | undefined>): Errors {
  const errors: Errors = {}
  for (const [key, message] of Object.entries(rules)) {
    if (message) errors[key] = message
  }
  return errors
}

export function hasErrors(errors: Errors): boolean {
  return Object.keys(errors).length > 0
}
