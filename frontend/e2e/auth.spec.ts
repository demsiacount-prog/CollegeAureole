import { test, expect } from '@playwright/test'
import { ADMIN_CREDENTIALS } from './helpers'

test.describe('Authentification', () => {
  test('connexion admin redirige vers /app et affiche le tableau de bord', async ({ page }) => {
    await page.goto('/connexion')
    await page.getByPlaceholder('prenom.nom@etablissement.com').fill(ADMIN_CREDENTIALS.email)
    await page.getByPlaceholder('••••••••').fill(ADMIN_CREDENTIALS.password)
    await page.getByRole('button', { name: 'Se connecter' }).click()
    await page.waitForURL('**/app')
    await expect(page.locator('main h1').first()).toBeVisible()
  })

  test('mauvais mot de passe affiche une erreur sans rediriger', async ({ page }) => {
    await page.goto('/connexion')
    await page.getByPlaceholder('prenom.nom@etablissement.com').fill(ADMIN_CREDENTIALS.email)
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
