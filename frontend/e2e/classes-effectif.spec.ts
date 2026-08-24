import { test, expect } from '@playwright/test'
import { login } from './helpers'

test('les élèves affectés à une classe sont visibles', async ({ page }) => {
  await login(page, 'admin')
  await page.goto('/app/classes')
  await expect(page.getByRole('heading', { name: 'Classes' })).toBeVisible()

  await page.getByRole('button', { name: 'Voir les élèves' }).first().click()

  const effectif = page.getByText(/élèves? inscrits? dans cette classe/)
  await expect(effectif).toBeVisible({ timeout: 10_000 })
  const count = parseInt((await effectif.textContent())?.match(/\d+/)?.[0] ?? '0', 10)

  if (count > 0) {
    await expect(page.locator('div.space-y-2 > div').first()).toBeVisible()
  }
})
