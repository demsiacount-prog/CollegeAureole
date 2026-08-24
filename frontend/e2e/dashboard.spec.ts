import { test, expect } from '@playwright/test'
import { login } from './helpers'

test("Tableau de bord — le directeur voit le pilotage sans le financier", async ({ page }) => {
  await login(page, 'directeur')
  await page.goto('/app')
  await expect(page.getByText('Bonjour, Directeur')).toBeVisible()
  await expect(page.locator('main').getByText("Taux d'absence", { exact: true })).toBeVisible()
  await expect(page.locator('main').getByText('Paiements', { exact: true })).toHaveCount(0)
})

test("Tableau de bord — le comptable voit les flux financiers", async ({ page }) => {
  await login(page, 'comptable')
  await page.goto('/app')
  await expect(page.getByText('Bonjour, Comptable')).toBeVisible()
  await expect(page.locator('main').getByText('Paiements du mois', { exact: true })).toBeVisible()
  await expect(page.locator('main').getByText('Dépenses du mois', { exact: true })).toBeVisible()
  await expect(page.locator('main').getByText('Échéances en retard', { exact: true })).toBeVisible()
  await expect(page.getByText('Impossible de charger les flux financiers')).toHaveCount(0)
})
