import { useState, type FormEvent } from 'react'
import { ServerCog, WifiOff } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { enregistrerServeur, verifierServeur, HOTE_LOCAL } from '@/lib/server'

/** Écran affiché quand aucun serveur (local par défaut en mono-poste) n'est
 *  joignable. Message simple orienté utilisateur final ; la saisie d'une
 *  adresse réseau reste possible pour l'administrateur. */
export function ServerSetup({ adresseInitiale }: { adresseInitiale?: string | null }) {
  const [adresse, setAdresse] = useState(adresseInitiale ?? '')
  const [erreur, setErreur] = useState<string | null>(null)
  const [teste, setTeste] = useState(false)
  const [avance, setAvance] = useState(false)

  async function tester(cible: string) {
    setErreur(null)
    setTeste(true)
    const resultat = await verifierServeur(cible)
    setTeste(false)
    if (resultat.ok) {
      enregistrerServeur(cible)
      window.location.reload()
    } else {
      setErreur(resultat.message)
    }
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (avance) {
      await tester(adresse)
    } else {
      await tester(HOTE_LOCAL)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[var(--color-base)] px-6 text-[var(--color-ink)]">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex size-14 items-center justify-center rounded-xl bg-[var(--color-surface-2)] ring-1 ring-[var(--color-border)]">
            <ServerCog size={26} strokeWidth={1.5} className="text-[var(--color-halo)]" />
          </div>
          <h1 className="font-[var(--font-display)] text-2xl font-semibold">Serveur introuvable</h1>
          <p className="mt-2 text-sm text-[var(--color-ink-dim)]">
            L’application n’a pas pu se connecter au serveur installé sur cet ordinateur.
            Vérifiez qu’il est bien démarré, puis réessayez.
          </p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="rounded-lg bg-[var(--color-surface)] p-6 shadow-[var(--shadow-soft)] ring-1 ring-[var(--color-border-soft)]"
        >
          <Button type="submit" variant="primary" className="w-full" isLoading={teste}>
            Réessayer
          </Button>

          <button
            type="button"
            onClick={() => setAvance((v) => !v)}
            className="mt-4 w-full text-center text-[11px] text-[var(--color-ink-faint)] underline"
          >
            {avance ? 'Masquer les options avancées' : 'Options avancées (administration)'}
          </button>

          {avance && (
            <div className="mt-4">
              <Input
                label="Adresse du serveur"
                placeholder={HOTE_LOCAL}
                value={adresse}
                onChange={(e) => setAdresse(e.target.value)}
                hint="Réservé à l’administration."
                autoFocus
              />
            </div>
          )}

          {erreur && (
            <p className="mt-3 flex items-start gap-2 rounded border border-[var(--color-danger-wash)] bg-[var(--color-danger-wash)] px-3 py-2 text-xs text-[var(--color-danger)]">
              <WifiOff size={14} strokeWidth={1.75} className="mt-0.5 shrink-0" />
              {erreur}
            </p>
          )}
        </form>

        <p className="mt-4 text-center text-[11px] leading-relaxed text-[var(--color-ink-faint)]">
          En cas de doute, contactez le responsable de l’établissement.
        </p>
      </div>
    </div>
  )
}
