import { test, expect, type APIRequestContext } from '@playwright/test'
import { login, apiContext } from './helpers'

const API_BASE = 'http://localhost:3001'

async function setupFixtures(api: APIRequestContext) {
  const annees = await (await api.get('/api/anneesScolaires/')).json()
  const anneeActive = (Array.isArray(annees) ? annees : annees.items).find((a: { active: boolean }) => a.active)

  const classes = await (await api.get('/api/classes/')).json()
  const classeList = Array.isArray(classes) ? classes : classes.items
  const classe6e = classeList.find((c: { niveau: string; nom: string }) => c.niveau === '6ème Année' && c.nom === 'A')
  const classe2e = classeList.find((c: { niveau: string; nom: string }) => c.niveau === '2ème Année' && c.nom === 'A')
  const classe3e = classeList.find((c: { niveau: string; nom: string }) => c.niveau === '3ème Année' && c.nom === 'A')

  const tuteurs = await (await api.get('/api/tuteurs/')).json()
  const tuteurList = Array.isArray(tuteurs) ? tuteurs : tuteurs.items
  const tuteurId = tuteurList.length > 0 ? tuteurList[0].id : null

  return { anneeActive, classe6e, classe2e, classe3e, tuteurId }
}

test.describe('Dossier élève — Inscription', () => {
  async function creerEleveSansInscription(api: APIRequestContext, tuteurId: number, suffix: string) {
    const rep = await api.post('/api/eleves/', {
      data: {
        nom: `Dossier${suffix}`, prenom: 'NonInscrit',
        date_de_naissance: '2012-05-10', lieu_de_naissance: 'Bamako',
        sexe: 'M', adresse: 'Badalabougou, Bamako', statut: 'actif',
        tuteur_id: tuteurId,
      },
    })
    expect(rep.status(), `création élève: ${await rep.text()}`).toBe(201)
    return (await rep.json()).matricule as string
  }

  test('élève non inscrit : inscription via le drawer, bouton masqué ensuite', async ({ page }) => {
    await login(page, 'admin')
    const api = await apiContext('admin')
    const { classe2e, tuteurId } = await setupFixtures(api)

    if (!tuteurId || !classe2e) {
      console.log('Skip: fixtures manquantes (tuteur ou classe 2ème)')
      await api.dispose()
      return
    }

    const matricule = await creerEleveSansInscription(api, tuteurId, 'A')
    await api.dispose()

    await page.goto(`/app/eleves/${matricule}`)
    await page.getByText(matricule).first().waitFor({ timeout: 15_000 })
    const main = page.locator('main')
    const boutonInscrire = main.getByRole('button', { name: 'Inscrire' })
    await expect(boutonInscrire).toBeVisible()

    await boutonInscrire.click()
    const drawer = page.locator('form')
    await drawer.getByLabel('Classe').selectOption({ label: `${classe2e.niveau} — ${classe2e.nom}` })
    await drawer.getByRole('button', { name: 'Inscrire' }).click()

    await expect(page.getByRole('button', { name: 'Modifier' })).toBeVisible({ timeout: 15_000 })
    await page.goto(`/app/eleves/${matricule}`)
    await page.getByText(matricule).first().waitFor({ timeout: 15_000 })
    await expect(page.locator('main').getByRole('button', { name: 'Inscrire' })).toHaveCount(0)
  })

  test('échec d\'inscription : message clair affiché et champs conservés', async ({ page }) => {
    await login(page, 'admin')
    const api = await apiContext('admin')
    const { anneeActive, classe3e, tuteurId } = await setupFixtures(api)

    if (!tuteurId || !classe3e || !anneeActive) {
      console.log('Skip: fixtures manquantes (tuteur, classe 3ème ou année active)')
      await api.dispose()
      return
    }

    const matricule = await creerEleveSansInscription(api, tuteurId, 'B')

    await page.goto(`/app/eleves/${matricule}`)
    await page.getByText(matricule).first().waitFor({ timeout: 15_000 })
    await page.locator('main').getByRole('button', { name: 'Inscrire' }).click()
    await page.getByLabel('Classe').selectOption({ label: `${classe3e.niveau} — ${classe3e.nom}` })

    const doublon = await api.post('/api/inscriptions/', {
      data: { matricule_eleve: matricule, id_classe: classe3e.id, id_annee_scolaire: anneeActive.id },
    })
    expect(doublon.status()).toBe(201)

    await page.locator('form').getByRole('button', { name: 'Inscrire' }).click()
    const alerte = page.locator('[role="alert"]')
    await expect(alerte).toBeVisible({ timeout: 15_000 })
    await expect(alerte).toContainText('déjà')
    await expect(page.getByLabel('Classe')).toHaveValue(String(classe3e.id))
    await api.dispose()
  })
})
