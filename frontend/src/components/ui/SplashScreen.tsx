import { useEffect, useState } from 'react'
import { GraduationCap } from 'lucide-react'
import { ProgressBar } from '@/components/ui/ProgressBar'

/** Design system §01 — Splash Screen & Démarrage.
 *  Écran plein (pas de sidebar/topbar), logo + halo ring animé, nom + devise,
 *  barre de progression 3px en bas (`--halo`), messages d'état en mono.
 *  Le pourcentage chiffré n'est jamais affiché. */
interface SplashScreenProps {
  /** Progression réelle 0–100 (la partie « déterminée » est ensuite gérée). */
  progress: number
  /** Message d'état courant (mono, affiché au-dessus de la barre). */
  message: string
  /** Version affichée en coin inférieur droit. */
  version?: string
  /** Nom affiché sous le logo (défaut : « Auréole »). */
  nom?: string
  /** Devise affichée sous le nom (Fraunces italic). */
  devise?: string
  /** Stoppe l'animation pulse du halo quand le chargement est terminé. */
  termine?: boolean
  /** Transforme le composant en écran d'erreur de démarrage. */
  erreur?: { titre: string; message: string; details?: string } | null
}

/** Séquence de démarrage §01, croisée en fondu (150 ms). */
function MessageEnFondu({ message }: { message: string }) {
  const [affiche, setAffiche] = useState(message)
  const [fondre, setFondre] = useState(false)

  useEffect(() => {
    if (message === affiche) return
    setFondre(true)
    const t = window.setTimeout(() => {
      setAffiche(message)
      setFondre(false)
    }, 150)
    return () => window.clearTimeout(t)
  }, [message, affiche])

  return (
    <span
      className="inline-block transition-opacity duration-150"
      style={{ opacity: fondre ? 0 : 1 }}
    >
      {affiche}
    </span>
  )
}

export function SplashScreen({
  progress,
  message,
  version,
  nom = 'Auréole',
  devise,
  termine = false,
  erreur = null,
}: SplashScreenProps) {
  if (erreur) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-[var(--color-base)] px-6 text-center">
        <span className="flex size-16 items-center justify-center rounded-full bg-[var(--color-danger-wash)]">
          <span className="font-[var(--font-mono)] text-2xl text-[var(--color-danger)]">✕</span>
        </span>
        <h1 className="mt-6 text-xl font-semibold text-[var(--color-danger)]">{erreur.titre}</h1>
        <p className="mt-2 max-w-md text-sm text-[var(--color-ink-dim)]">{erreur.message}</p>
        {erreur.details && (
          <div className="mt-6 w-full max-w-lg text-left">
            <p className="mb-1 text-xs font-semibold text-[var(--color-ink)]">Détails techniques</p>
            <pre className="max-h-48 overflow-auto rounded-[var(--radius-sm)] border border-[var(--color-border)] bg-[var(--color-surface)] p-3 font-[var(--font-mono)] text-[11px] leading-relaxed text-[var(--color-ink-faint)]">
              {erreur.details}
            </pre>
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="relative flex min-h-screen flex-col items-center justify-center overflow-hidden bg-[var(--color-base)] px-6">
      <div className="flex flex-col items-center">
        <span className={`relative flex size-20 items-center justify-center ${termine ? '' : 'animate-halo-pulse'}`}>
          <span className="absolute inset-0 rounded-full halo-ring" />
          <span className="flex size-16 items-center justify-center rounded-full border border-[var(--color-halo-dim)] bg-[var(--color-surface)]">
            <GraduationCap className="size-8 text-[var(--color-halo)]" strokeWidth={1.5} />
          </span>
        </span>
        <h1 className="mt-6 font-[var(--font-display)] text-[32px] font-semibold text-[var(--color-ink)]">{nom}</h1>
        {devise && (
          <p className="mt-1 font-[var(--font-display)] text-[13px] italic text-[var(--color-halo-dim)]">{devise}</p>
        )}
      </div>

      <div className="absolute inset-x-0 bottom-0">
        <p className="mb-6 text-center font-[var(--font-mono)] text-xs text-[var(--color-ink-faint)]">
          <MessageEnFondu message={message} />
        </p>
        <ProgressBar variant="splash" value={progress} />
      </div>

      {version && (
        <p className="absolute bottom-4 right-4 text-[10px] text-[var(--color-ink-faint)]">v{version}</p>
      )}
    </div>
  )
}