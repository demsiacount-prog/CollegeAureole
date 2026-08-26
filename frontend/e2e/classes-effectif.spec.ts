import { test, expect } from '@playwright/test'
import { login } from './helpers'

test('les classes affichent leur effectif', async ({ page }) => {
  await login(page, 'admin')
  await page.goto('/app/classes')
  await expect(page.getByRole('heading', { name: 'Classes' })).toBeVisible()

  const rows = page.locator('tbody tr')
  const count = await rows.count()

  if (count > 0) {
    await page.getByRole('button', { name: 'Voir les élèves' }).first().click()
    const effectif = page.getByText(/élèves? inscrits? dans cette classe/)
    await expect(effectif).toBeVisible({ timeout: 10_000 })
  } else {
    await expect(page.getByText('Aucune classe')).toBeVisible()
  }
})
