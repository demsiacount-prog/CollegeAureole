import { test, expect } from '@playwright/test'

test.describe('Authentification', () => {
  test('connexion admin redirige vers /app et affiche le tableau de bord', async ({ page }) => {
    await page.goto('/connexion')
    await page.getByPlaceholder('prenom.nom@etablissement.com').fill('admin@etablissement.com')
    await page.getByPlaceholder('••••••••').fill('Password123!')
    await page.getByRole('button', { name: 'Se connecter' }).click()
    await page.waitForURL('**/app')
    await expect(page.locator('main h1').first()).toBeVisible()
  })

  test('mauvais mot de passe affiche une erreur sans rediriger', async ({ page }) => {
    await page.goto('/connexion')
    await page.getByPlaceholder('prenom.nom@etablissement.com').fill('admin@etablissement.com')
    await page.getByPlaceholder('••••••••').fill('MotDePasseErrone')
    await page.getByRole('button', { name: 'Se connecter' }).click()
    await expect(page.getByRole('alert')).toBeVisible()
    await expect(page).toHaveURL(/\/connexion/)
  })

  test('accès à /app sans session redirige vers /connexion', async ({ page }) => {
    await page.goto('/app')
    await expect(page).toHaveURL(/\/connexion/)
  })
})
