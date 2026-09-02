import { useEffect, useState } from 'react'
import { SplashScreen } from '@/components/ui/SplashScreen'
import { ServerSetup } from '@/pages/ServerSetup'
import { estDesktop, getServeur, HOTE_LOCAL, enregistrerServeur, verifierServeur } from '@/lib/server'

type Statut = 'verification' | 'configuration' | 'pret'

/** Séquence de démarrage §01 : vérifications en arrière-plan du client bureau. */
const SEQUENCE = [
  { seuil: 0, message: 'Démarrage de College Aureole…' },
  { seuil: 15, message: 'Vérification de la base de données…' },
  { seuil: 35, message: 'Connexion au serveur local…' },
  { seuil: 55, message: 'Chargement des configurations…' },
  { seuil: 75, message: 'Vérification de l’instance…' },
  { seuil: 90, message: 'Préparation de l’interface…' },
  { seuil: 100, message: 'Prêt !' },
]

function messagePourProgress(progress: number): string {
  let dernier = SEQUENCE[0].message
  for (const etape of SEQUENCE) {
    if (progress >= etape.seuil) dernier = etape.message
  }
  return dernier
}

/** Garde-fou du client bureau : s'assure qu'un serveur (local par
 *  défaut en mono-poste) est joignable avant d'afficher l'application.
 *  Sans effet en mode web. */
export function ServerGate({ children }: { children: React.ReactNode }) {
  const [statut, setStatut] = useState<Statut>(() => (!estDesktop() ? 'pret' : 'verification'))
  const [adresseInitiale, setAdresseInitiale] = useState<string | null>(null)
  const [progress, setProgress] = useState(0)

  useEffect(() => {
    if (!estDesktop()) return
    let annule = false

    async function seConnecter() {
      setProgress(15)
      // Tente l'adresse mémorisée si elle existe.
      const memorise = getServeur()
      if (memorise) {
        setProgress(35)
        const r = await verifierServeur(memorise)
        if (annule) return
        if (r.ok) {
          setProgress(55)
          setStatut('pret')
          return
        }
      }

      // Sinon tente automatiquement l'hôte local (mono-poste).
      setProgress(55)
      const local = await verifierServeur(HOTE_LOCAL)
      if (annule) return
      if (local.ok) {
        enregistrerServeur(HOTE_LOCAL)
        setProgress(75)
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
    return <SplashScreen progress={progress} message={messagePourProgress(progress)} />
  }
  if (estDesktop()) return <ServerSetup adresseInitiale={adresseInitiale} />
  return <>{children}</>
}
