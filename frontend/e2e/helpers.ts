import { request, type Page } from '@playwright/test'

const CREDENTIALS: Record<string, { email: string; password: string }> = {
  admin: { email: 'admin@collegeaureole.ml', password: 'Password123!' },
  directeur: { email: 'directeur@collegeaureole.ml', password: 'Password123!' },
  comptable: { email: 'comptable@collegeaureole.ml', password: 'Password123!' },
}

export async function loginViaApi(page: Page, role: 'admin' | 'directeur' | 'comptable' = 'admin') {
  const creds = CREDENTIALS[role]
  const ctx = await request.newContext({ baseURL: 'http://localhost:3000' })
  const res = await ctx.post('/api/auth/connexion', {
    data: { email: creds.email, mot_de_passe: creds.password },
  })
  if (res.status() !== 200) throw new Error(`Login API échoué (${res.status()})`)
  const body = await res.json()
  await ctx.dispose()
  await page.goto('/connexion')
  await page.evaluate((token) => {
    localStorage.setItem('aureole_token', token)
    localStorage.setItem('aureole-install-id', 'e2e-install')
    localStorage.setItem('aureole-demo-state-web-e2e-install', '1')
  }, body.access_token)
  await page.goto('/app')
  await page.locator('main h2').first().waitFor({ timeout: 15_000 })
}

export const ROUTES: { label: string; path: string }[] = [
  { label: 'Tableau de bord', path: '/app' },
  { label: 'Élèves', path: '/app/eleves' },
  { label: 'Enseignants', path: '/app/enseignants' },
  { label: 'Tuteurs', path: '/app/tuteurs' },
  { label: 'Classes', path: '/app/classes' },
  { label: 'Salles', path: '/app/salles' },
  { label: 'Inscriptions', path: '/app/inscriptions' },
  { label: 'Absences', path: '/app/absences' },
  { label: 'Notes', path: '/app/notes' },
  { label: 'Bulletins', path: '/app/bulletins' },
  { label: 'Résultats', path: '/app/resultats' },
  { label: 'Cours', path: '/app/cours' },
  { label: 'Emploi du temps', path: '/app/seances' },
  { label: 'Paiements', path: '/app/paiements' },
  { label: 'Dépenses', path: '/app/depenses' },
  { label: 'Clôture d’année', path: '/app/cloture-annee' },
  { label: 'Paramètres', path: '/app/parametres' },
]
