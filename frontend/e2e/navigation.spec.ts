import { test, expect } from '@playwright/test'
import { login, ROUTES } from './helpers'

test.describe('Navigation — chaque page se charge sans crash', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, 'admin')
  })

  for (const route of ROUTES) {
    test(`rendu ${route.label} (${route.path})`, async ({ page }) => {
      const pageErrors: string[] = []
      page.on('pageerror', (err) => pageErrors.push(String(err)))

      await page.goto(route.path)
      await expect(page.locator('main h1').first()).toBeVisible({ timeout: 20_000 })

      const boundaryVisible = await page
        .getByText('Une erreur est survenue', { exact: false })
        .isVisible()
        .catch(() => false)

      expect(boundaryVisible, 'ErreurBoundary affiché').toBe(false)
      expect(pageErrors, `pageerror: ${pageErrors.join(' | ')}`).toEqual([])
    })
  }
})
