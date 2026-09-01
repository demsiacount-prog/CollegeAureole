import { useEffect, useState } from 'react'
import { Spinner } from '@/components/ui/Spinner'
import { ServerSetup } from '@/pages/ServerSetup'
import { estDesktop, getServeur, HOTE_LOCAL, enregistrerServeur, verifierServeur } from '@/lib/server'

type Statut = 'verification' | 'configuration' | 'pret'

/** Garde-fou du client bureau : s'assure qu'un serveur (local par
 *  défaut en mono-poste) est joignable avant d'afficher l'application.
 *  Sans effet en mode web. */
export function ServerGate({ children }: { children: React.ReactNode }) {
  const [statut, setStatut] = useState<Statut>(() => (!estDesktop() ? 'pret' : 'verification'))
  const [adresseInitiale, setAdresseInitiale] = useState<string | null>(null)

  useEffect(() => {
    if (!estDesktop()) return
    let annule = false

    async function seConnecter() {
      // Tente l'adresse mémorisée si elle existe.
      const memorise = getServeur()
      if (memorise) {
        const r = await verifierServeur(memorise)
        if (annule) return
        if (r.ok) {
          setStatut('pret')
          return
        }
      }

      // Sinon tente automatiquement l'hôte local (mono-poste).
      const local = await verifierServeur(HOTE_LOCAL)
      if (annule) return
      if (local.ok) {
        enregistrerServeur(HOTE_LOCAL)
        setStatut('pret')
        return
      }

      // Aucun serveur joignable : affiche l'écran de configuration simple.
      setAdresseInitiale(memorise ?? HOTE_LOCAL)
      setStatut('configuration')
    }

    seConnecter()
    return () => { annule = true }
  }, [])

  if (estDesktop() && statut === 'pret') return <>{children}</>
  if (estDesktop() && statut === 'verification') {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[var(--color-base)]">
        <Spinner label="Recherche du serveur…" />
      </div>
    )
  }
  if (estDesktop()) return <ServerSetup adresseInitiale={adresseInitiale} />
  return <>{children}</>
}
