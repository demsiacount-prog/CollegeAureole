import { request, type APIRequestContext, type Page } from '@playwright/test'

export const API_BASE = 'http://localhost:3001'

/** Compte unique d'administration (rôles supprimés depuis v5). */
export const ADMIN_CREDENTIALS = { email: 'admin@etablissement.com', password: 'Password123!' }

/** Connexion via le formulaire de connexion réel (workflow utilisateur). */
export async function login(page: Page) {
  const creds = ADMIN_CREDENTIALS
  await page.goto('/')
  await page.evaluate(() => localStorage.removeItem('aureole_token'))
  await page.goto('/connexion')
  await page.getByPlaceholder('prenom.nom@etablissement.com').fill(creds.email)
  await page.getByPlaceholder('••••••••').fill(creds.password)
  await page.getByRole('button', { name: 'Se connecter' }).click()
  await page.waitForURL('**/app', { timeout: 15_000 })
  await page.locator('nav').first().waitFor({ timeout: 15_000 })
}

/** Connexion via l'API — utilitaire quand le formulaire n'est pas l'objet du test. */
export async function loginViaApi(page: Page) {
  const creds = ADMIN_CREDENTIALS
  const ctx = await request.newContext({ baseURL: API_BASE })
  const res = await ctx.post('/api/auth/connexion', {
    data: { email: creds.email, mot_de_passe: creds.password },
  })
  if (res.status() !== 200) throw new Error(`Login API échoué (${res.status()})`)
  const body = await res.json()
  await ctx.dispose()
  await page.goto('/connexion')
  await page.evaluate((token) => {
    localStorage.setItem('aureole_token', token)
  }, body.access_token)
  await page.goto('/app')
  await page.locator('nav').first().waitFor({ timeout: 15_000 })
}

/** Contexte API authentifié (3001) : vérifications et nettoyage. */
export async function apiContext(): Promise<APIRequestContext> {
  const creds = ADMIN_CREDENTIALS
  const auth = await request.newContext({ baseURL: API_BASE })
  const res = await auth.post('/api/auth/connexion', {
    data: { email: creds.email, mot_de_passe: creds.password },
  })
  if (res.status() !== 200) throw new Error(`Login API échoué (${res.status()})`)
  const { access_token } = await res.json()
  await auth.dispose()
  return request.newContext({
    baseURL: API_BASE,
    extraHTTPHeaders: { Authorization: `Bearer ${access_token}` },
  })
}

export const ROUTES: { label: string; path: string }[] = [
  { label: 'Tableau de bord', path: '/app' },
  { label: 'Élèves', path: '/app/eleves' },
  { label: 'Classes', path: '/app/classes' },
  { label: 'Inscriptions', path: '/app/inscriptions' },
  { label: 'Tuteurs', path: '/app/tuteurs' },
  { label: 'Enseignants', path: '/app/enseignants' },
  { label: 'Cours', path: '/app/cours' },
  { label: 'Notes', path: '/app/notes' },
  { label: 'Bulletins', path: '/app/bulletins' },
  { label: 'Résultats', path: '/app/resultats' },
  { label: 'Séances', path: '/app/seances' },
  { label: 'Absences', path: '/app/absences' },
  { label: 'Paiements', path: '/app/paiements' },
  { label: 'Dépenses', path: '/app/depenses' },
  { label: 'Salles', path: '/app/salles' },
  { label: 'Documents administratifs', path: '/app/documents' },
  { label: 'Clôture d’année', path: '/app/cloture-annee' },
  { label: 'Paramètres', path: '/app/parametres' },
]
