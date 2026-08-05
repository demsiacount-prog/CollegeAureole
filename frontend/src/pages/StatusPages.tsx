import { ShieldAlert, Compass } from 'lucide-react'
import { Button } from '@/components/ui/Button'

export function AccessDeniedPage() {
  return (
    <div className="flex flex-col items-center justify-center gap-4 py-24 text-center">
      <ShieldAlert className="size-10 text-[var(--color-danger)]" strokeWidth={1.75} />
      <div>
        <h2 className="text-xl font-semibold text-[var(--color-ink)]">Accès refusé</h2>
        <p className="mt-1.5 max-w-sm text-sm text-[var(--color-ink-dim)]">
          Votre rôle ne permet pas d’accéder à cette section.
        </p>
      </div>
      <Button variant="secondary" to="/app">
        Retour au tableau de bord
      </Button>
    </div>
  )
}

export function NotFoundPage() {
  return (
    <div className="flex h-screen w-full flex-col items-center justify-center gap-4 bg-[var(--color-base)] text-center">
      <Compass className="size-10 text-[var(--color-brand)]" strokeWidth={1.75} />
      <div>
        <h2 className="text-xl font-semibold text-[var(--color-ink)]">Page introuvable</h2>
        <p className="mt-1.5 text-sm text-[var(--color-ink-dim)]">Cette page n’existe pas ou plus.</p>
      </div>
      <Button variant="primary" to="/app">
        Retour à l’accueil
      </Button>
    </div>
  )
}
