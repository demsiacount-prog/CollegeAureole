import { describe, expect, it } from 'vitest'
import { extractErrorMessage } from './api'

// On construit de faux AxiosError sans dépendre du réseau : extractErrorMessage
// ne fait que lire error.response, et axios.isAxiosError() se contente de
// vérifier le marqueur `isAxiosError` (duck-typing), reproduit ici.
function fauxErreurAxios(overrides: { response?: { status: number; data?: unknown } }) {
  return { isAxiosError: true, ...overrides }
}

describe('extractErrorMessage', () => {
  it('erreur réseau (pas de réponse) -> message de connectivité', () => {
    const err = fauxErreurAxios({ response: undefined })
    expect(extractErrorMessage(err)).toMatch(/contacter le serveur/i)
  })

  it('utilise data.message si présent', () => {
    const err = fauxErreurAxios({ response: { status: 400, data: { message: 'Élève introuvable.' } } })
    expect(extractErrorMessage(err)).toBe('Élève introuvable.')
  })

  it('utilise data.detail si c’est une chaîne', () => {
    const err = fauxErreurAxios({ response: { status: 404, data: { detail: 'Classe introuvable.' } } })
    expect(extractErrorMessage(err)).toBe('Classe introuvable.')
  })

  it('utilise data.detail.message si detail est un objet', () => {
    const err = fauxErreurAxios({
      response: { status: 409, data: { detail: { message: 'Ce post est déjà publié.' } } },
    })
    expect(extractErrorMessage(err)).toBe('Ce post est déjà publié.')
  })

  it('BUG CONFIRMÉ : un champ manquant n’est PAS annoncé comme "requis"', () => {
    // FastAPI/Pydantic v2 (vérifié empiriquement contre le backend réel, cf.
    // rapport de revue) répond, pour un champ manquant :
    //   {"type": "missing", "loc": [...], "msg": "Field required"}
    // `_detailLisible` ne reçoit que `msg` (pas `type`) et cherche le mot
    // "missing" DANS `msg` — qui contient en réalité "Field required" et ne
    // matche donc jamais. La branche "est requis(e)" est du code mort : un
    // champ manquant retombe sur le message générique "est invalide", ce qui
    // induit l'utilisateur en erreur (il croit avoir saisi une valeur
    // incorrecte alors qu'il n'a simplement rien saisi).
    const err = fauxErreurAxios({
      response: {
        status: 422,
        data: { detail: [{ type: 'missing', loc: ['body', 'email'], msg: 'Field required' }] },
      },
    })
    expect(extractErrorMessage(err)).toBe("L'adresse e-mail est invalide.")
  })

  it('traduit une erreur de longueur minimale avec le libellé du champ', () => {
    const err = fauxErreurAxios({
      response: {
        status: 422,
        data: {
          detail: [
            { loc: ['body', 'mot_de_passe'], msg: 'String should have at least 8 characters' },
          ],
        },
      },
    })
    expect(extractErrorMessage(err)).toMatch(/mot de passe doit comporter au moins 8 caractères/i)
  })

  it('regroupe au plus 3 erreurs de validation', () => {
    const detail = Array.from({ length: 5 }, (_, i) => ({ loc: ['body', `champ${i}`], msg: 'field required' }))
    const err = fauxErreurAxios({ response: { status: 422, data: { detail } } })
    const messages = extractErrorMessage(err).split('. ').filter(Boolean)
    expect(messages.length).toBeLessThanOrEqual(3)
  })

  it('erreur 500 sans détail exploitable -> message générique serveur', () => {
    const err = fauxErreurAxios({ response: { status: 500, data: {} } })
    expect(extractErrorMessage(err)).toMatch(/erreur interne/i)
  })

  it('erreur sans corps exploitable et sans statut serveur -> repli fourni', () => {
    const err = fauxErreurAxios({ response: { status: 400, data: undefined } })
    expect(extractErrorMessage(err, 'Repli personnalisé.')).toBe('Repli personnalisé.')
  })

  it('objet qui n’est pas une erreur axios -> repli', () => {
    expect(extractErrorMessage(new Error('boom'), 'Repli.')).toBe('Repli.')
    expect(extractErrorMessage('texte quelconque')).toBe('Une erreur est survenue.')
  })
})
