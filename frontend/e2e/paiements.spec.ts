import { test, expect, request } from '@playwright/test'
import { login } from './helpers'

test('paiements : recherche dans le sélect et création', async ({ page }) => {
  await login(page, 'admin')

  const ctx = await request.newContext({ baseURL: 'http://localhost:3001' })
  const authRes = await ctx.post('/api/auth/connexion', {
    data: { email: 'admin@etablissement.com', mot_de_passe: 'Password123!' },
  })
  const { access_token } = await authRes.json()
  const auth = { headers: { Authorization: `Bearer ${access_token}` } }

  const tuteur = await ctx.post('/api/tuteurs/', {
    data: { nom: 'PaiT', prenom: 'Tuteur', email: `tuteur.pai${Date.now()}@etablissement.com`, telephone: '+223 76 99 88 77' },
    headers: auth.headers,
  })
  expect(tuteur.status()).toBe(201)

  const eleve = await ctx.post('/api/eleves/', {
    data: {
      nom: `PaiTest${Date.now()}`, prenom: 'Élève', date_de_naissance: '2011-06-15',
      lieu_de_naissance: 'Bamako', sexe: 'M', statut: 'actif',
      tuteur_id: (await tuteur.json()).id,
    },
    headers: auth.headers,
  })
  expect(eleve.status()).toBe(201)
  const matricule = (await eleve.json()).matricule

  const annees = await (await ctx.get('/api/anneesScolaires/', auth)).json()
  const anneeActive = (Array.isArray(annees) ? annees : annees.items).find((a: { active: boolean }) => a.active)

  if (anneeActive) {
    const classe = await ctx.post('/api/classes/', {
      data: {
        niveau: '6ème',
        nom: `PaiClasse${Date.now()}`,
        frais_inscription: 5000,
        mensualite: 2000,
      },
      headers: auth.headers,
    })
    expect(classe.status()).toBe(201)
    await ctx.post('/api/inscriptions/', {
      data: { matricule_eleve: matricule, id_classe: (await classe.json()).id, id_annee_scolaire: anneeActive.id },
      headers: auth.headers,
    })
  }
  await ctx.dispose()

  await page.goto('/app/paiements')
  await expect(page.getByRole('heading', { name: 'Paiements' })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Nouveau paiement' })).toBeVisible()

  await page.getByRole('button', { name: 'Nouveau paiement' }).click()
  await expect(page.getByRole('heading', { name: 'Enregistrer un paiement' })).toBeVisible()

  const combobox = page.locator('form input[role="combobox"]')
  await expect(combobox).toBeVisible()
  await combobox.fill('PaiTest')
  await expect(page.getByRole('option').first()).toContainText(/PaiTest/i)
  await page.getByRole('option').first().click()

  await page.getByLabel('Montant (FCFA)').fill('1000')
  await page.getByRole('button', { name: 'Enregistrer' }).click()
  await expect(page.getByText(/Paiement enregistré/)).toBeVisible()

  await expect(page.getByRole('table')).toBeVisible()
  await expect(page.getByRole('table')).toContainText(matricule)
})
