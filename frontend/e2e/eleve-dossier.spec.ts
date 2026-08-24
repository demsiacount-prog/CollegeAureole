import { test, expect } from '@playwright/test'
import { login } from './helpers'

const MATRICULE = 'EL2500001'
const API_BASE = 'http://localhost:3001'

test.describe('Dossier élève — Résultats & Absences', () => {
  test('onglet Résultats : historique par année, le clic révèle les notes', async ({ page }) => {
    await login(page, 'admin')
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

  test('onglet Absences : regroupées par année, l\'année active prime', async ({ page, request }) => {
    await login(page, 'admin')

    const token = await page.evaluate(() => localStorage.getItem('aureole_token'))
    const auth = { headers: { Authorization: `Bearer ${token}` } }

    // Référence : données réelles de l'élève (indépendantes du seed)
    const dossier = await (await request.get(`${API_BASE}/api/eleves/${MATRICULE}/dossier`, auth)).json()
    const ancienneAnnee = dossier.annee_scolaire
    const absencesAncienne = dossier.absences
    const nAbs = absencesAncienne.length
    const nomsCours = [...new Set(absencesAncienne.map((a) => a.cours?.nom).filter(Boolean))]
    const aUneNonJustifiee = absencesAncienne.some((a) => !a.justifiee)

    // Fixtures : année scolaire suivante active + inscription de l'élève
    let nouvelleAnneeId: number | undefined
    let inscriptionId: number | undefined
    try {
      const create = await request.post(`${API_BASE}/api/anneesScolaires/`, {
        data: { libelle: '2026-2027', date_debut: '2026-10-01', date_fin: '2027-07-31', active: true },
        headers: auth.headers,
      })
      expect(create.status()).toBe(201)
      nouvelleAnneeId = (await create.json()).id

      const insc = await request.post(`${API_BASE}/api/inscriptions/`, {
        data: { matricule_eleve: MATRICULE, id_classe: 2, id_annee_scolaire: nouvelleAnneeId },
        headers: auth.headers,
      })
      expect(insc.status()).toBe(201)
      inscriptionId = (await insc.json()).id

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
      await expect(ancienne).toContainText(`${nAbs} absence${nAbs > 1 ? 's' : ''}`)

      await expect(main.locator('tbody tr')).toHaveCount(0)

      await ancienne.click()
      await expect(main.locator('tbody tr')).toHaveCount(nAbs)
      for (const nom of nomsCours) {
        await expect(main.getByText(nom, { exact: true }).first()).toBeVisible()
      }
      if (aUneNonJustifiee) {
        await expect(main.getByText('Non justifiée', { exact: true }).first()).toBeVisible()
      }
    } finally {
      if (inscriptionId != null) {
        await request.delete(`${API_BASE}/api/inscriptions/${inscriptionId}`, { headers: auth.headers })
      }
      await request.put(`${API_BASE}/api/anneesScolaires/${ancienneAnnee.id}/activer`, { headers: auth.headers })
      if (nouvelleAnneeId != null) {
        await request.delete(`${API_BASE}/api/anneesScolaires/${nouvelleAnneeId}`, { headers: auth.headers })
      }
    }
  })
})

test.describe('Dossier élève — Inscription', () => {
  async function creerEleveSansInscription(request: import('@playwright/test').APIRequestContext, auth: { headers: Record<string, string> }, suffix: string) {
    const tuteurs = await (await request.get(`${API_BASE}/api/tuteurs/`, auth)).json()
    const tuteurId = (Array.isArray(tuteurs) ? tuteurs : tuteurs.items)[0].id
    const rep = await request.post(`${API_BASE}/api/eleves/`, {
      data: {
        nom: `Dossier${suffix}`, prenom: 'NonInscrit',
        date_de_naissance: '2012-05-10', lieu_de_naissance: 'Bamako',
        sexe: 'M', adresse: 'Badalabougou, Bamako', statut: 'actif',
        tuteur_id: tuteurId,
      },
      headers: auth.headers,
    })
    expect(rep.status()).toBe(201)
    return (await rep.json()).matricule as string
  }

  test('élève non inscrit : inscription via le drawer, bouton masqué ensuite', async ({ page, request }) => {
    await login(page, 'admin')
    const token = await page.evaluate(() => localStorage.getItem('aureole_token'))
    const auth = { headers: { Authorization: `Bearer ${token}` } }
    const matricule = await creerEleveSansInscription(request, auth, 'A')

    // Élève créé sans inscription → le bouton « Inscrire » est disponible.
    await page.goto(`/app/eleves/${matricule}`)
    await page.getByText(matricule).first().waitFor({ timeout: 15_000 })
    const main = page.locator('main')
    const boutonInscrire = main.getByRole('button', { name: 'Inscrire' })
    await expect(boutonInscrire).toBeVisible()

    await boutonInscrire.click()
    const drawer = page.locator('form')
    await drawer.getByLabel('Classe').selectOption({ label: '2ème Année — A' })
    await drawer.getByRole('button', { name: 'Inscrire' }).click()

    // Succès : le drawer se referme, l'inscription apparaît…
    await expect(page.getByRole('button', { name: 'Modifier' })).toBeVisible({ timeout: 15_000 })
    // …et l'élève étant maintenant inscrit, le bouton ne revient pas (refetch).
    await page.goto(`/app/eleves/${matricule}`)
    await page.getByText(matricule).first().waitFor({ timeout: 15_000 })
    await expect(page.locator('main').getByRole('button', { name: 'Inscrire' })).toHaveCount(0)
  })

  test('échec d\'inscription : message clair affiché et champs conservés', async ({ page, request }) => {
    await login(page, 'admin')
    const token = await page.evaluate(() => localStorage.getItem('aureole_token'))
    const auth = { headers: { Authorization: `Bearer ${token}` } }
    const matricule = await creerEleveSansInscription(request, auth, 'B')

    await page.goto(`/app/eleves/${matricule}`)
    await page.getByText(matricule).first().waitFor({ timeout: 15_000 })
    await page.locator('main').getByRole('button', { name: 'Inscrire' }).click()
    await page.getByLabel('Classe').selectOption({ label: '3ème Année — A' })

    // Conflit : la même inscription est créée en parallèle via l'API.
    const annees = await (await request.get(`${API_BASE}/api/anneesScolaires/`, auth)).json()
    const anneeActive = (Array.isArray(annees) ? annees : annees.items).find((a: { active: boolean }) => a.active)
    const classes = await (await request.get(`${API_BASE}/api/classes/`, auth)).json()
    const classe3e = (Array.isArray(classes) ? classes : classes.items).find((c: { niveau: string; nom: string }) => c.niveau === '3ème Année' && c.nom === 'A')
    const doublon = await request.post(`${API_BASE}/api/inscriptions/`, {
      data: { matricule_eleve: matricule, id_classe: classe3e.id, id_annee_scolaire: anneeActive.id },
      headers: auth.headers,
    })
    expect(doublon.status()).toBe(201)

    // La soumission UI échoue alors : erreur explicite, champs conservés.
    await page.locator('form').getByRole('button', { name: 'Inscrire' }).click()
    const alerte = page.locator('[role="alert"]')
    await expect(alerte).toBeVisible({ timeout: 15_000 })
    await expect(alerte).toContainText('déjà')
    await expect(page.getByLabel('Classe')).toHaveValue(String(classe3e.id))
  })
})
