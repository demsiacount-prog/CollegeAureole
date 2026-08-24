import { test, expect } from '@playwright/test'
import { login } from './helpers'

test.describe('CRUD UI — salle (créer / voir / supprimer)', () => {
  test('création, présence en liste puis suppression', async ({ page }) => {
    await login(page, 'admin')
    await page.goto('/app/salles')

    const nom = `__TEST__ UI ${Date.now()}`
    await page.getByRole('button', { name: 'Nouvelle salle' }).click()
    await page.getByLabel('Nom').fill(nom)
    await page.getByRole('button', { name: 'Créer' }).click()

    const recherche = page.getByPlaceholder('Rechercher une salle…')
    await recherche.fill(nom)
    await expect(page.getByText(nom, { exact: true }).first()).toBeVisible({ timeout: 15_000 })

    await page.getByRole('button', { name: `Supprimer ${nom}` }).click()
    await page.getByRole('button', { name: 'Supprimer', exact: true }).click()

    await expect(page.getByText('Aucune salle ne correspond à cette recherche.')).toBeVisible({
      timeout: 15_000,
    })
  })
})
