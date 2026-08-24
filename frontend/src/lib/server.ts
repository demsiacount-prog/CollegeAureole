// Gestion du poste-serveur pour le client bureau (Tauri).
//
// En mode web, l'API est jointe sur la même origine (proxy vite en dev,
// même domaine en production) — comportement historique inchangé.
// En mode bureau, l'interface tourne depuis tauri://localhost : il faut une
// adresse explicite vers le poste-serveur, mémorisée au premier lancement.

export const SERVEUR_STORAGE_KEY = 'aureole_serveur'

/** Vrai si l'interface s'exécute dans la fenêtre Tauri. */
export function estDesktop(): boolean {
  return typeof window !== 'undefined' && '__TAURI_INTERNALS__' in window
}

/** Adresse du poste-serveur mémorisée (null tant que non configurée). */
export function getServeur(): string | null {
  if (!estDesktop()) return null
  const brut = localStorage.getItem(SERVEUR_STORAGE_KEY)
  const propre = brut?.trim().replace(/\/+$/, '')
  return propre || null
}

export function enregistrerServeur(url: string): string {
  const propre = url.trim().replace(/\/+$/, '')
  localStorage.setItem(SERVEUR_STORAGE_KEY, propre)
  return propre
}

export function oublierServeur(): void {
  localStorage.removeItem(SERVEUR_STORAGE_KEY)
}

/** Base à utiliser pour les appels axios (chaîne vide = chemins relatifs). */
export function resoudreBaseUrl(): string {
  if (estDesktop()) return getServeur() ?? ''
  return import.meta.env.VITE_API_URL || (typeof window !== 'undefined' ? window.location.origin : '')
}

/**
 * Rend absolus les chemins servis par le backend (/uploads/…) afin qu'ils
 * pointent vers le poste-serveur en mode bureau ; sans effet en mode web.
 */
export function urlAbsolue<T extends string | null | undefined>(chemin: T): T {
  if (!chemin) return chemin
  if (/^(https?:|blob:|data:)/i.test(chemin)) return chemin
  if (!chemin.startsWith('/')) return chemin
  const base = estDesktop() ? getServeur() : ''
  if (!base) return chemin
  return `${base}${chemin}` as T
}

export interface ResultatVerification {
  ok: boolean
  message: string
}

/** Teste la joignabilité d'un poste-serveur (GET /api/health). */
export async function verifierServeur(adresse: string): Promise<ResultatVerification> {
  const cible = adresse.trim().replace(/\/+$/, '')
  if (!cible) return { ok: false, message: 'Veuillez saisir l’adresse du serveur.' }
  if (!/^https?:\/\//i.test(cible)) {
    return { ok: false, message: 'L’adresse doit commencer par http:// ou https://.' }
  }

  const controleur = new AbortController()
  const minuteur = setTimeout(() => controleur.abort(), 5000)
  try {
    const reponse = await fetch(`${cible}/api/health`, { signal: controleur.signal })
    if (!reponse.ok) {
      return { ok: false, message: `Le serveur a répondu avec une erreur (${reponse.status}).` }
    }
    const donnees = await reponse.json().catch(() => null)
    if (donnees?.status !== 'running') {
      return { ok: false, message: 'Réponse inattendue du serveur.' }
    }
    if (donnees?.database !== 'connected') {
      return { ok: false, message: 'Le serveur répond mais sa base de données est inaccessible.' }
    }
    return { ok: true, message: 'Connexion au serveur établie.' }
  } catch {
    return {
      ok: false,
      message: `Impossible de joindre ${cible}. Vérifiez que l’application serveur est démarrée sur le poste-serveur et que cette adresse est correcte.`,
    }
  } finally {
    clearTimeout(minuteur)
  }
}
