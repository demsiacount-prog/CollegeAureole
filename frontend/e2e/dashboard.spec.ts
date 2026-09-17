import { test, expect } from '@playwright/test'
import { login } from './helpers'

test('Tableau de bord — l’administrateur consulte le pilotage', async ({ page }) => {
  await login(page)
  await page.goto('/app')
  await expect(page.locator('main h1').first()).toBeVisible()
})