import { useEffect, useState } from 'react'
import { Spinner } from '@/components/ui/Spinner'
import { ServerSetup } from '@/pages/ServerSetup'
import { estDesktop, getServeur, verifierServeur } from '@/lib/server'

type Statut = 'verification' | 'configuration' | 'pret'

/** Garde-fou du client bureau : tant qu'aucun poste-serveur n'est configuré
 *  (ou s'il est injoignable), l'écran de configuration est affiché à la place
 *  de l'application. Sans effet en mode web. */
export function ServerGate({ children }: { children: React.ReactNode }) {
  const [statut, setStatut] = useState<Statut>(() => (!estDesktop() || getServeur() ? 'verification' : 'configuration'))
  const [adresseInitiale, setAdresseInitiale] = useState<string | null>(null)

  useEffect(() => {
    if (!estDesktop()) return
    const serveur = getServeur()
    if (!serveur) return
    let annule = false
    verifierServeur(serveur).then((resultat) => {
      if (annule) return
      if (resultat.ok) setStatut('pret')
      else {
        setAdresseInitiale(serveur)
        setStatut('configuration')
      }
    })
    return () => { annule = true }
  }, [])

  if (!estDesktop() || statut === 'pret') return <>{children}</>
  if (statut === 'verification') {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[var(--color-base)]">
        <Spinner label="Recherche du serveur…" />
      </div>
    )
  }
  return <ServerSetup adresseInitiale={adresseInitiale} />
}
