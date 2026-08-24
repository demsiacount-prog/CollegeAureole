import { test, expect, request } from '@playwright/test'
import { login } from './helpers'

test('paiements : nom de l’élève affiché, pas d’avatar, recherche dans le sélect', async ({ page }) => {
  await login(page, 'admin')
  await page.goto('/app/paiements')
  await expect(page.getByRole('heading', { name: 'Paiements' })).toBeVisible()

  await expect(page.getByRole('table')).toBeVisible()

  const first = page.getByRole('table').locator('tbody tr').first()
  await expect(first).toContainText(/EL[0-9]+/)
  const nomCell = first.locator('td').nth(2)
  await expect(nomCell.locator('a')).toContainText(/[A-Za-zÀ-ÿ]+/)
  await expect(nomCell).not.toContainText('—')

  expect(await page.getByRole('table').locator('img').count()).toBe(0)

  // Les données d'exemple étant générées aléatoirement, le nom recherché
  // est récupéré depuis l'API plutôt que codé en dur.
  const ctx = await request.newContext({ baseURL: 'http://localhost:3001' })
  const authRes = await ctx.post('/api/auth/connexion', {
    data: { email: 'admin@etablissement.com', mot_de_passe: 'Password123!' },
  })
  const { access_token } = await authRes.json()
  const elevesRes = await ctx.get('/api/eleves/', {
    headers: { Authorization: `Bearer ${access_token}` },
  })
  const eleves = await elevesRes.json()
  await ctx.dispose()
  const nomEleve = eleves[0].nom as string

  await page.getByRole('button', { name: 'Nouveau paiement' }).click()
  await expect(page.getByRole('heading', { name: 'Enregistrer un paiement' })).toBeVisible()

  const combobox = page.locator('form input[role="combobox"]')
  await expect(combobox).toBeVisible()
  await combobox.fill(nomEleve)
  await expect(page.getByRole('option').first()).toContainText(new RegExp(nomEleve, 'i'))
  await page.getByRole('option').first().click()

  await expect(combobox).toHaveValue(new RegExp(nomEleve, 'i'))

  await expect(page.getByLabel('N° reçu')).toHaveCount(0)

  await page.getByLabel('Montant (FCFA)').fill('1000')
  await page.getByRole('button', { name: 'Enregistrer' }).click()
  await expect(page.getByText(/Paiement enregistré/)).toBeVisible()
})
