// Journal de débogage de l'authentification.
//
// Inactif par défaut. Pour l'activer, dans la console du navigateur :
//   localStorage.setItem('AUREOLE_TRACE', '1')
// puis recharger la page et reproduire la déconnexion.
// Le journal est écrit dans la console (niveau info) avec le préfixe
// [auth-trace]. Pour lire les traces : prefetch... ouvrir la console aussi
// tôt que possible et sélectionner « Verbose ».
export function trace(...args: unknown[]): void {
  if (typeof window === 'undefined') return
  try {
    if (localStorage.getItem('AUREOLE_TRACE') === '1') {
      // eslint-disable-next-line no-console
      console.info('[auth-trace]', ...args)
    }
  } catch {
    /* localStorage inaccessible : on ne journalise pas. */
  }
}