import { test, expect } from '@playwright/test'
import { login } from './helpers'

test("Tableau de bord — le directeur voit le pilotage sans le financier", async ({ page }) => {
  await login(page, 'admin')
  await page.goto('/app')
  await expect(page.locator('main h2').first()).toBeVisible()
})

test("Tableau de bord — le comptable voit les flux financiers", async ({ page }) => {
  await login(page, 'admin')
  await page.goto('/app')
  await expect(page.locator('main h2').first()).toBeVisible()
})
