import { Link } from 'react-router-dom'
import { ShieldAlert, Compass } from 'lucide-react'

export function AccessDeniedPage() {
  return (
    <div className="flex flex-col items-center justify-center gap-4 py-24 text-center">
      <ShieldAlert className="size-10 text-[var(--color-danger)]" strokeWidth={1.5} />
      <div>
        <h2 className="font-[var(--font-display)] text-xl font-medium text-[var(--color-ink)]">Accès refusé</h2>
        <p className="mt-1.5 max-w-sm text-sm text-[var(--color-ink-dim)]">
          Votre rôle ne permet pas d’accéder à cette section.
        </p>
      </div>
      <Link
        to="/app"
        className="rounded-[var(--radius-sm)] border border-[var(--color-border)] bg-[var(--color-surface-3)] px-4 py-2 text-sm font-medium text-[var(--color-ink)] transition-colors hover:bg-[var(--color-surface-2)]"
      >
        Retour au tableau de bord
      </Link>
    </div>
  )
}

export function NotFoundPage() {
  return (
    <div className="flex h-screen w-full flex-col items-center justify-center gap-4 bg-[var(--color-base)] text-center">
      <Compass className="size-10 text-[var(--color-halo)]" strokeWidth={1.5} />
      <div>
        <h2 className="font-[var(--font-display)] text-xl font-medium text-[var(--color-ink)]">Page introuvable</h2>
        <p className="mt-1.5 text-sm text-[var(--color-ink-dim)]">Cette page n’existe pas ou plus.</p>
      </div>
      <Link
        to="/app"
        className="rounded-[var(--radius-sm)] bg-[var(--color-halo)] px-4 py-2 text-sm font-medium text-[#161208] transition-colors hover:bg-[var(--color-halo-bright)]"
      >
        Retour à l’accueil
      </Link>
    </div>
  )
}
