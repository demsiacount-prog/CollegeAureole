import { useState, type FormEvent } from 'react'
import { ServerCog, WifiOff } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { enregistrerServeur, verifierServeur } from '@/lib/server'

/** Écran de premier lancement du client bureau : saisie et test de
 *  l'adresse du poste-serveur. Une fois la connexion validée, l'adresse est
 *  mémorisée et l'application redémarre normalement. */
export function ServerSetup({ adresseInitiale }: { adresseInitiale?: string | null }) {
  const [adresse, setAdresse] = useState(adresseInitiale ?? '')
  const [erreur, setErreur] = useState<string | null>(null)
  const [teste, setTeste] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setErreur(null)
    setTeste(true)
    const resultat = await verifierServeur(adresse)
    if (resultat.ok) {
      enregistrerServeur(adresse)
      window.location.reload()
    } else {
      setErreur(resultat.message)
      setTeste(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[var(--color-base)] px-6 text-[var(--color-ink)]">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex size-14 items-center justify-center rounded-xl bg-[var(--color-surface-2)] ring-1 ring-[var(--color-border)]">
            <ServerCog size={26} strokeWidth={1.5} className="text-[var(--color-halo)]" />
          </div>
          <h1 className="font-[var(--font-display)] text-2xl font-semibold">Connexion au serveur</h1>
          <p className="mt-2 text-sm text-[var(--color-ink-dim)]">
            Indiquez l’adresse du poste sur lequel l’application serveur College Aureole est installée.
            Cette information n’est demandée qu’une seule fois.
          </p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="rounded-lg bg-[var(--color-surface)] p-6 shadow-[var(--shadow-soft)] ring-1 ring-[var(--color-border-soft)]"
        >
          <Input
            label="Adresse du serveur"
            placeholder="http://192.168.1.10:8000"
            value={adresse}
            onChange={(e) => setAdresse(e.target.value)}
            hint="Exemple : http://192.168.1.10:8000 (port indiqué lors de l’installation du serveur)."
            autoFocus
          />

          {erreur && (
            <p className="mt-3 flex items-start gap-2 rounded border border-[var(--color-danger-wash)] bg-[var(--color-danger-wash)] px-3 py-2 text-xs text-[var(--color-danger)]">
              <WifiOff size={14} strokeWidth={1.75} className="mt-0.5 shrink-0" />
              {erreur}
            </p>
          )}

          <Button type="submit" variant="primary" className="mt-5 w-full" isLoading={teste}>
            Tester et se connecter
          </Button>
        </form>

        <p className="mt-4 text-center text-[11px] leading-relaxed text-[var(--color-ink-faint)]">
          En cas de doute, demandez l’adresse au responsable de l’établissement.
        </p>
      </div>
    </div>
  )
}
