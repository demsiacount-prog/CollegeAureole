import { test, expect } from '@playwright/test'
import { loginViaApi } from './helpers'

const MATRICULE = 'EL2500001'

test.describe('Dossier élève — Résultats & Absences', () => {
  test('onglet Résultats : historique par année, le clic révèle les notes', async ({ page }) => {
    await loginViaApi(page, 'admin')
    await page.goto(`/app/eleves/${MATRICULE}`)
    await page.getByText(MATRICULE, { exact: true }).first().waitFor({ timeout: 15_000 })

    const main = page.locator('main')
    await main.getByRole('button', { name: /Résultats/ }).click()

    const annee = main.getByRole('button', { name: /2025-2026/ })
    await expect(annee).toBeVisible()
    await expect(annee).toContainText('9 périodes')
    await expect(annee).toContainText('Moy. annuelle')

    await expect(main.getByText('Composition 1', { exact: true })).toBeVisible()
    await expect(main.getByText('Note /10', { exact: true }).first()).toBeVisible()

    await annee.click()
    await expect(main.getByText('Composition 1', { exact: true })).toBeHidden()
    await annee.click()
    await expect(main.getByText('Composition 1', { exact: true })).toBeVisible()
  })

  test('onglet Absences : regroupées par année, l\'année active prime', async ({ page }) => {
    await loginViaApi(page, 'admin')
    await page.goto(`/app/eleves/${MATRICULE}`)
    await page.getByText(MATRICULE, { exact: true }).first().waitFor({ timeout: 15_000 })

    const main = page.locator('main')
    const ongletAbsences = main.getByRole('button', { name: /Absences/ })
    await expect(ongletAbsences).toContainText('0')

    await ongletAbsences.click()

    const active = main.getByRole('button', { name: /2026.?2027/ })
    await expect(active).toBeVisible()
    await expect(active).toContainText('0 absence')
    await expect(main.getByText("Aucune absence pour l'année active.")).toBeVisible()

    const ancienne = main.getByRole('button', { name: /2025-2026/ })
    await expect(ancienne).toBeVisible()
    await expect(ancienne).toContainText('2 absences')

    await expect(main.locator('tbody tr')).toHaveCount(0)

    await ancienne.click()
    await expect(main.locator('tbody tr')).toHaveCount(2)
    await expect(main.getByText('Langue Nationale (Bambara) — 5ème Année')).toBeVisible()
    await expect(main.getByText('Lecture / Écriture — 5ème Année')).toBeVisible()
    await expect(main.getByText('Non justifiée', { exact: true }).first()).toBeVisible()
  })
})
