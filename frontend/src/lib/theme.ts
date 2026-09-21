const STORAGE_KEY = 'aureole-theme'

/** Applique le thème avant le premier rendu React (module externe, donc
 * autorisé par la CSP `script-src 'self'`). Remplace l'ancien script inline
 * de `index.html`, bloqué par la CSP au build (flash de thème). */
export function appliquerThemeInitial(): void {
  const stored = localStorage.getItem(STORAGE_KEY)
  const theme =
    stored === 'light' || stored === 'dark'
      ? stored
      : window.matchMedia('(prefers-color-scheme: light)').matches
        ? 'light'
        : 'dark'
  document.documentElement.setAttribute('data-theme', theme)
  document.documentElement.style.colorScheme = theme
}