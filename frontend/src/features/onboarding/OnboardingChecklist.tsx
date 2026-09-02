import { useMemo } from 'react'
import { CheckCircle2, X } from 'lucide-react'
import { useAuth } from '@/auth/useAuth'

const STORAGE_KEY = 'aureole_onboarding'

function lireFerme(): boolean {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) return JSON.parse(raw).banniereFermee === true
  } catch {
    /* silencieux */
  }
  return false
}

function fermer() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ banniereFermee: true }))
  } catch {
    /* silencieux */
  }
}

export function OnboardingChecklist() {
  const { user } = useAuth()
  const masque = useMemo(lireFerme, [])

  if (!user || masque) return null

  return (
    <div
      className="relative flex items-start gap-4 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-5 py-5 sm:items-center"
      style={{ borderTop: '2px solid var(--color-halo)' }}
    >
      <span className="halo-ring flex size-10 shrink-0 items-center justify-center rounded-full">
        <CheckCircle2 className="size-5 text-[var(--color-halo)]" strokeWidth={1.75} />
      </span>
      <div className="min-w-0 flex-1">
        <h2 className="font-[var(--font-display)] text-[22px] font-semibold leading-tight text-[var(--color-ink)]">
          College Aureole est prêt !
        </h2>
        <p className="mt-0.5 text-sm text-[var(--color-ink-dim)]">
          Votre instance est configurée. Commencez par ajouter vos premiers élèves ou configurez l'emploi du temps.
        </p>
      </div>
      <button
        type="button"
        onClick={fermer}
        className="shrink-0 rounded-md p-1.5 text-[var(--color-ink-faint)] transition-colors hover:bg-[var(--color-surface-2)] hover:text-[var(--color-ink)]"
        aria-label="Fermer le bandeau de bienvenue"
      >
        <X className="size-4" strokeWidth={2} />
      </button>
    </div>
  )
}
