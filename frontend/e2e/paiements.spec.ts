import { test, expect } from '@playwright/test'
import { loginViaApi } from './helpers'

test('paiements : nom de l’élève affiché, pas d’avatar, recherche dans le sélect', async ({ page }) => {
  await loginViaApi(page, 'admin')
  await page.goto('/app/paiements')
  await expect(page.getByRole('heading', { name: 'Paiements' })).toBeVisible()

  await expect(page.getByRole('table')).toBeVisible()

  const first = page.getByRole('table').locator('tbody tr').first()
  await expect(first).toContainText(/EL[0-9]+/)
  const nomCell = first.locator('td').nth(2)
  await expect(nomCell.locator('a')).toContainText(/[A-Za-zÀ-ÿ]+/)
  await expect(nomCell).not.toContainText('—')

  expect(await page.getByRole('table').locator('img').count()).toBe(0)

  await page.getByRole('button', { name: 'Nouveau paiement' }).click()
  await expect(page.getByRole('heading', { name: 'Enregistrer un paiement' })).toBeVisible()

  const combobox = page.locator('form input[role="combobox"]')
  await expect(combobox).toBeVisible()
  await combobox.fill('Breton')
  await expect(page.getByRole('option').first()).toContainText('Breton')
  await page.getByRole('option').first().click()

  await expect(combobox).toHaveValue(/Breton/)

  await expect(page.getByLabel('N° reçu')).toHaveCount(0)

  await page.getByLabel('Montant (FCFA)').fill('1000')
  await page.getByRole('button', { name: 'Enregistrer' }).click()
  await expect(page.getByText(/reçu REC-\d+/)).toBeVisible()
})
