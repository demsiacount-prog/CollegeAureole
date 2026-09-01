import { test, expect, request, type Page } from '@playwright/test'

const ADMIN_EMAIL = 'admin@etablissement.com'
const ADMIN_PASSWORD = 'Password123!'
const DEVISE = 'L’excellence en toute épreuve'

const ROUTES_APP: { label: string; path: string }[] = [
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

const LOGO_PNG = Buffer.from(
  'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==',
  'base64',
)

async function loginInit(page: Page) {
  const ctx = await request.newContext({ baseURL: 'http://localhost:3001' })
  const res = await ctx.post('/api/auth/connexion', {
    data: { email: ADMIN_EMAIL, mot_de_passe: ADMIN_PASSWORD },
  })
  if (res.status() !== 200) throw new Error(`Login API échoué (${res.status()}): ${await res.text()}`)
  const body = await res.json()
  await ctx.dispose()
  await page.goto('/connexion')
  await page.evaluate((token) => {
    localStorage.setItem('aureole_token', token)
  }, body.access_token)
  await page.goto('/app')
  await page.locator('main h1').first().waitFor({ timeout: 15_000 })
}

test.describe('Assistant d’initialisation', () => {
  test.setTimeout(120_000)

  test('configure l’établissement puis crée le compte admin', async ({ page }) => {
    await page.goto('/')

    // Écran 1 : fiche établissement
    await expect(page.getByRole('heading', { name: 'Configuration initiale' })).toBeVisible()
    await page.getByLabel('Nom de l’établissement').fill('Collège Auréole e2e')
    await page.getByLabel('Sigle').fill('CA')
    await page.getByLabel('Devise').fill(DEVISE)
    await page.getByLabel('Adresse').fill('Bamako, Mali')
    await page.getByLabel('Académie').fill('Académie de Bamako')
    await page.getByLabel('CAP').fill('CA-2025')
    await page.getByLabel('Téléphone').fill('+223 12 34 56 78')
    await page.getByLabel('E-mail de contact').fill('contact@etablissement.com')
    await page.locator('input[type="file"]').setInputFiles({
      name: 'logo.png',
      mimeType: 'image/png',
      buffer: LOGO_PNG,
    })
    await expect(
      page.locator('img[src^="/uploads/logos/"]').first(),
    ).toBeVisible({ timeout: 10_000 })
    await page.getByRole('button', { name: 'Continuer' }).click()

    // Écran 2 : compte administrateur
    await expect(page.getByRole('heading', { name: 'Compte administrateur' })).toBeVisible()
    await page.getByLabel('Nom', { exact: true }).fill('Admin')
    await page.getByLabel('Prénom', { exact: true }).fill('Système')
    await page.getByLabel('Adresse e-mail administrateur').fill(ADMIN_EMAIL)
    await page.locator('#setup-password').fill(ADMIN_PASSWORD)
    await page.getByRole('button', { name: 'Continuer' }).click()

    // Écran 3 : année scolaire
    await expect(page.getByRole('heading', { name: 'Année scolaire' })).toBeVisible()
    await page.locator('#date-debut').fill('2025-09-15')
    await page.locator('#date-fin').fill('2026-07-04')
    await page.getByRole('button', { name: 'Initialiser l’établissement' }).click()

    // L'initialisation réussit : l'administrateur créé est connecté automatiquement
    // puis redirigé vers l'application.
    await expect(page).toHaveURL(/\/app/, { timeout: 60_000 })
    await expect(page.locator('main h1').first()).toBeVisible({ timeout: 15_000 })
  })

  test('une fois configuré, l’application ne montre plus l’assistant', async ({ page }) => {
    // Le serveur (et sa base) est partagé entre les tests : la configuration
    // du test précédent est déjà en place.
    await page.goto('/')
    await expect(page).toHaveURL(/\/connexion/)
    await expect(page.getByRole('heading', { name: 'Configuration initiale' })).toHaveCount(0)
  })

  test('la fiche établissement est consultable et modifiable dans Paramètres', async ({ page }) => {
    const ctx = await request.newContext({ baseURL: 'http://localhost:3001' })
    const res = await ctx.post('/api/auth/connexion', {
      data: { email: ADMIN_EMAIL, mot_de_passe: ADMIN_PASSWORD },
    })
    if (res.status() !== 200) throw new Error(`Login API échoué (${res.status()})`)
    const body = await res.json()
    await ctx.dispose()
    await page.goto('/connexion')
    await page.evaluate((token) => {
      localStorage.setItem('aureole_token', token)
    }, body.access_token)
    await page.goto('/app/parametres')
    await page.locator('main h1').first().waitFor({ timeout: 15_000 })

    await page.getByRole('button', { name: 'Fiche établissement' }).click()
    await expect(page.getByText('Collège Auréole e2e').first()).toBeVisible()
    await expect(page.getByLabel('Téléphone')).toHaveValue('+223 12 34 56 78')

    // Académie et CAP : saisis dans l'assistant, ils apparaissent dans la fiche.
    await expect(page.getByLabel('Académie')).toHaveValue('Académie de Bamako')
    await expect(page.getByLabel('CAP')).toHaveValue('CA-2025')
    await expect(page.getByText('Académie de Bamako').first()).toBeVisible()
    await expect(page.getByText('CA-2025').first()).toBeVisible()

    // Import du logo : un aperçu apparaît, puis l'enregistrement le persiste.
    await page.locator('input[type="file"]').setInputFiles({
      name: 'logo.png',
      mimeType: 'image/png',
      buffer: LOGO_PNG,
    })
    const logoPreview = page.locator('main img[src^="/uploads/logos/"]')
    await expect(logoPreview).toBeVisible({ timeout: 10_000 })

    await page.getByLabel('Téléphone').fill('+223 00 11 22 33')
    await page.getByRole('button', { name: 'Enregistrer' }).click()
    await expect(page.getByText('Fiche établissement mise à jour.')).toBeVisible()
    await expect(logoPreview).toBeVisible()
  })

  test('parcours complet : chaque module se charge sans erreur', async ({ page }) => {
    await loginInit(page)

    // L'application reprend l'identité saisie dans l'assistant (nom + devise).
    const aside = page.locator('aside')
    await expect(aside.getByText('Collège Auréole e2e').first()).toBeVisible()
    await expect(aside.getByText(DEVISE).first()).toBeVisible()

    const pageErrors: string[] = []
    page.on('pageerror', (err) => pageErrors.push(String(err)))

    for (const route of ROUTES_APP) {
      await page.goto(route.path)
      await expect(page.locator('main h1').first()).toBeVisible({ timeout: 20_000 })
      const boundary = await page
        .getByText('Une erreur est survenue', { exact: false })
        .isVisible()
        .catch(() => false)
      expect(boundary, `ErreurBoundary sur ${route.path}`).toBe(false)
    }
    expect(pageErrors, `pageerror: ${pageErrors.join(' | ')}`).toEqual([])
  })


  test('la fiche établissement pilote l’application : devise et logo dans la sidebar', async ({ page }) => {
    await loginInit(page)
    await page.goto('/app/parametres')
    await page.getByRole('button', { name: 'Fiche établissement' }).click()
    await expect(page.getByLabel('Devise')).toBeVisible()

    // La devise saisie dans la fiche s'affiche sous le nom, dans la sidebar.
    await page.getByLabel('Devise').fill('Éduquer, c’est révéler')
    await page.getByRole('button', { name: 'Enregistrer' }).click()
    await expect(page.getByText('Fiche établissement mise à jour.')).toBeVisible()
    await expect(page.locator('aside').getByText('Éduquer, c’est révéler').first()).toBeVisible()

    // Le logo importé remplace l'emblème par défaut dans la sidebar (après enregistrement).
    await page.locator('input[type="file"]').setInputFiles({
      name: 'logo.png',
      mimeType: 'image/png',
      buffer: LOGO_PNG,
    })
    const asideLogo = page.locator('aside img[src^="/uploads/logos/"]')
    await expect(page.locator('main img[src^="/uploads/logos/"]').first()).toBeVisible({ timeout: 10_000 })
    await page.getByRole('button', { name: 'Enregistrer' }).click()
    await expect(page.getByText('Fiche établissement mise à jour.').first()).toBeVisible()
    await expect(asideLogo).toBeVisible()
  })
})
