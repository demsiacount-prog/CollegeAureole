import axios from 'axios'
import { resoudreBaseUrl } from './server'
import { trace } from './trace'

export const TOKEN_STORAGE_KEY = 'aureole_token'

// Empreinte courte d'un token pour le journal de débogage (jamais le JWT complet).
export function traceToken(token: string | null): string {
  if (!token) return '<aucun>'
  return `${token.slice(0, 12)}…${token.slice(-4)}`
}

// L'API est appelée sur le backend FastAPI. En mode web, la même origine sert
// l'interface et relaie /api vers le backend (proxy vite en dev) ; VITE_API_URL
// reste un sur-ensemble pour pointer explicitement vers une autre adresse.
// En mode bureau (Tauri), la base est résolue à chaque requête depuis
// l'adresse du serveur local mémorisée (lib/server.ts).
export const api = axios.create({
  baseURL: resoudreBaseUrl() || undefined,
  timeout: 30_000,
})

api.interceptors.request.use((config) => {
  config.baseURL = resoudreBaseUrl() || undefined
  const token = localStorage.getItem(TOKEN_STORAGE_KEY)
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
    // Mémorise le token de la requête (identifiant unique de la session au
    // moment de son émission) : permet de distinguer une réponse 401 d'un
    // ancien token d'une vraie expiration de la session courante.
    ;(config as { _jwt?: string })._jwt = token
  }
  if (String(config.url ?? '').startsWith('/api/')) {
    trace('→ requête', config.method?.toUpperCase(), config.url, 'jwt=', traceToken(token))
  }
  return config
})

export const AUTH_EXPIRED_EVENT = 'aureole:auth-expired'

api.interceptors.response.use(
  (response) => {
    if (String(response.config.url ?? '').startsWith('/api/')) {
      trace('← réponse', response.status, response.config.method?.toUpperCase(), response.config.url)
    }
    return response
  },
  (error) => {
    // Une 401 peut provenir d'une requête émise AVANT une reconnexion (ex.
    // /api/auth/moi démarré au chargement avec un ancien token périmé, lent
    // à répondre). Si la requête utilisait un token différent de la session
    // actuelle, cette réponse tardive ne doit pas déconnecter l'utilisateur
    // qui vient de se (re)connecter. On ne signale l'expiration que pour un
    // token toujours courant (ou une requête sans token : /connexion, 401 de
    // mauvaise identification, sans session à préserver).
    if (error.response?.status === 401) {
      const tokenRequete = (error.config as { _jwt?: string } | undefined)?._jwt
      const tokenCourant = localStorage.getItem(TOKEN_STORAGE_KEY)
      // Une 401 consécutive à une redirection 307 cross-origine (requête sans
      // slash final, FastAPI renvoie la bonne URL absolue vers le serveur)
      // voit l'en-tête Authorization retiré par le navigateur : ce n'est pas
      // une session expirée. On ne déconnecte que si la réponse 401 vient bien
      // de l'origine prévue.
      const urlFinale = (error.response.request as { responseURL?: string } | undefined)?.responseURL
      const base = resoudreBaseUrl()
      let memeOrigine = true
      try {
        if (urlFinale && base) {
          memeOrigine = new URL(base).origin === new URL(urlFinale).origin
        }
      } catch {
        /* URL mal formée : on ne se fie pas à ce test */
      }
      // Une session n'est expirée QUE si la requête elle-même portait le token
      // courant et que le serveur (même origine) l'a refusée.
      const expireSession = !!tokenRequete && tokenRequete === tokenCourant && memeOrigine
      trace(
        '! 401', error.config?.method?.toUpperCase(), error.config?.url,
        'jwt requête=', traceToken(tokenRequete ?? null),
        'jwt courant=', traceToken(tokenCourant),
        expireSession ? '→ DECONNEXION' : '→ ignoré (ancien token, hors origine ou non authentifié)',
      )
      if (expireSession) {
        window.dispatchEvent(new CustomEvent(AUTH_EXPIRED_EVENT))
      }
    } else if (error.response?.status) {
      trace('! erreur HTTP', error.response.status, error.config?.method?.toUpperCase(), error.config?.url)
    } else {
      trace('! erreur réseau', error.config?.method?.toUpperCase(), error.config?.url, String(error.message ?? error))
    }
    return Promise.reject(error)
  },
)

// Traduction des codes de validation Pydantic/FastAPI en libellés compréhensibles.
const CHAMP_LABELS: Record<string, string> = {
  nom: 'le nom', prenom: 'le prénom', email: "l'adresse e-mail",
  telephone: 'le numéro de téléphone', adresse: "l'adresse",
  date_naissance: 'la date de naissance', date_de_naissance: 'la date de naissance',
  lieu_naissance: 'le lieu de naissance', lieu_de_naissance: 'le lieu de naissance',
  sexe: 'le sexe', password: 'le mot de passe', mot_de_passe: 'le mot de passe',
  matricule: 'le matricule', matricule_eleve: "l'élève", matricule_enseignant: "l'enseignant",
  tuteur_id: 'le tuteur', classe_id: 'la classe', id_classe: 'la classe',
  niveau: 'le niveau', salle_id: 'la salle', id_salle: 'la salle',
  id_annee_scolaire: "l'année scolaire", annee_scolaire_id: "l'année scolaire",
  montant: 'le montant', note: 'la note', bareme: 'le barème',
  specialite: 'la spécialité', photo: 'la photo', statut: 'le statut',
  observation: "l'observation", motif: 'le motif', date_absence: "la date d'absence",
  justifiee: 'la justification', libelle: 'le libellé', date_debut: 'la date de début',
  date_fin: 'la date de fin', frais_inscription: 'les frais d’inscription',
  mensualite: 'la mensualité', profession: 'la profession',
}

function _detailLisible(msg: string, loc?: unknown): string {
  const champ = Array.isArray(loc) ? String(loc[loc.length - 1]) : undefined
  const label = champ ? CHAMP_LABELS[champ] : undefined
  if (/missing/i.test(msg)) return `${label ? `${labelCapitalise(label)} est requis(e)` : 'Un champ obligatoire est manquant'}.`
  const nb = msg.match(/ensure the value has at least (\d+) characters|String should have at least (\d+) characters/i)
  if (nb) return `${label ? `${labelCapitalise(label)} doit comporter au moins` : 'Le champ doit comporter au moins'} ${nb[1] ?? nb[2]} caractères.`
  if (/greater than or equal|Input should be a valid number/i.test(msg) && label) return `${labelCapitalise(label)} est invalide.`
  if (/not a valid|unable to parse/i.test(msg)) return `${label ? `${labelCapitalise(label)} est invalide` : 'La valeur saisie est invalide'}.`
  return label ? `${labelCapitalise(label)} est invalide.` : 'Certaines informations saisies sont invalides.'
}

function labelCapitalise(label: string): string {
  return label.charAt(0).toUpperCase() + label.slice(1)
}

export function extractErrorMessage(error: unknown, fallback = 'Une erreur est survenue.'): string {
  if (axios.isAxiosError(error)) {
    if (!error.response) {
      return 'Impossible de contacter le serveur. Vérifiez votre connexion puis réessayez.'
    }
    const data = error.response.data as
      | { message?: string; detail?: unknown }
      | undefined
    if (data) {
      if (typeof data.message === 'string') return data.message
      if (typeof data.detail === 'string') return data.detail
      // Erreurs de validation FastAPI (422) : tableau de { loc, msg }.
      if (Array.isArray(data.detail)) {
        const premiers = data.detail
          .map((d) => _detailLisible(String((d as { msg?: string }).msg ?? ''), (d as { loc?: unknown }).loc))
          .slice(0, 3)
        return premiers.join(' ')
      }
      if (
        data.detail &&
        typeof data.detail === 'object' &&
        typeof (data.detail as { message?: unknown }).message === 'string'
      ) {
        return (data.detail as { message: string }).message
      }
    }
    if (error.response.status >= 500) {
      return 'Une erreur interne est survenue côté serveur. Réessayez ; si le problème persiste, contactez l’administrateur.'
    }
  }
  return fallback
}
