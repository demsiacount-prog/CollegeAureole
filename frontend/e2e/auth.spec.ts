import { test, expect } from '@playwright/test'

test.describe('Authentification', () => {
  test('connexion admin redirige vers /app et affiche le tableau de bord', async ({ page }) => {
    await page.goto('/connexion')
    await page.getByPlaceholder('prenom.nom@aureole.ml').fill('admin@collegeaureole.ml')
    await page.getByPlaceholder('••••••••').fill('Password123!')
    await page.getByRole('button', { name: 'Se connecter' }).click()
    await page.waitForURL('**/app')
    await expect(page.locator('main h2').first()).toBeVisible()
  })

  test('mauvais mot de passe affiche une erreur sans rediriger', async ({ page }) => {
    await page.goto('/connexion')
    await page.getByPlaceholder('prenom.nom@aureole.ml').fill('admin@collegeaureole.ml')
    await page.getByPlaceholder('••••••••').fill('MotDePasseErrone')
    await page.getByRole('button', { name: 'Se connecter' }).click()
    await expect(page.getByRole('alert')).toBeVisible()
    await expect(page).toHaveURL(/\/connexion/)
  })

  test('accès à /app sans session redirige vers /connexion', async ({ page }) => {
    await page.goto('/app')
    await expect(page).toHaveURL(/\/connexion/)
  })

  test('connexion directeur et comptable fonctionnent', async ({ page }) => {
    for (const role of [
      { email: 'directeur@collegeaureole.ml', label: 'directeur' },
      { email: 'comptable@collegeaureole.ml', label: 'comptable' },
    ]) {
      await page.goto('/connexion')
      await page.evaluate(() => localStorage.clear())
      await page.reload()
      await page.getByPlaceholder('prenom.nom@aureole.ml').fill(role.email)
      await page.getByPlaceholder('••••••••').fill('Password123!')
      await page.getByRole('button', { name: 'Se connecter' }).click()
      await page.waitForURL('**/app')
      await expect(page.locator('main h2').first()).toBeVisible()
    }
  })
})
