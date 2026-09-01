import { test, expect, request, type APIRequestContext } from '@playwright/test'
import { login } from './helpers'

const BASE_URL = 'http://localhost:3001'
const PREFIX = `NOTES E2E ${Date.now()}`

async function creerApiContexte(): Promise<APIRequestContext> {
  const auth = await request.newContext({ baseURL: BASE_URL })
  const res = await auth.post('/api/auth/connexion', {
    data: { email: 'admin@etablissement.com', mot_de_passe: 'Password123!' },
  })
  if (res.status() !== 200) throw new Error(`Login API échoué (${res.status()})`)
  const { access_token } = await res.json()
  await auth.dispose()
  return request.newContext({
    baseURL: BASE_URL,
    extraHTTPHeaders: { Authorization: `Bearer ${access_token}` },
  })
}

async function creerAnnee(api: APIRequestContext, libelle?: string): Promise<{ anneeId: number; trimestreId: number }> {
  const anneeRes = await api.post('/api/anneesScolaires/', {
    data: { libelle: libelle ?? `${PREFIX} — Année`, date_debut: '2026-01-05', date_fin: '2026-12-20', active: false },
  })
  expect(anneeRes.ok(), `création année (${anneeRes.status()}): ${await anneeRes.text()}`).toBeTruthy()
  const annee = await anneeRes.json()

  const trimestres = await (
    await api.get('/api/trimestres/', { params: { annee_scolaire_id: annee.id, limit: 500 } })
  ).json()
  expect(trimestres.some((t: { type: string }) => t.type === 'TRIMESTRE')).toBeTruthy()
  const composition = trimestres.find((t: { type: string }) => t.type === 'COMPOSITION')
  if (!composition) throw new Error('Aucune composition auto-générée')
  return { anneeId: annee.id, trimestreId: composition.id }
}

async function creerFixtures(api: APIRequestContext) {
  const ens = await api.post('/api/enseignants/', {
    data: {
      nom: 'NoteTest', prenom: 'Prof', email: `prof.notetest${Date.now()}@etablissement.com`,
      telephone: '+223 76 10 20 30', adresse: 'Bamako', specialite: 'Mathématiques',
    },
  })
  expect(ens.status()).toBe(201)
  const matriculeEns = (await ens.json()).matricule

  const salle = await api.post('/api/salles/', { data: { nom: `Salle Notes ${Date.now()}` } })
  expect(salle.status()).toBe(201)

  const classe = await api.post('/api/classes/', { data: { niveau: '6ème Année', nom: `N${Date.now()}` } })
  expect(classe.status()).toBe(201)
  const classeData = await classe.json()
  const classeId = classeData.id
  const classeNom = `6ème Année — ${classeData.nom}`

  const coursNom = `Maths Notes ${Date.now()}`
  const cours = await api.post('/api/cours/', {
    data: {
      nom: coursNom, description: '', volume_horaire: 2,
      matricule_enseignant: matriculeEns,
      affectations: [{ id_classe: classeId, coefficient: 1 }],
    },
  })
  expect(cours.status()).toBe(201)
  const coursId = (await cours.json()).id

  const tuteur = await api.post('/api/tuteurs/', {
    data: {
      nom: 'NoteTuteur', prenom: 'T', email: `tuteur.note${Date.now()}@etablissement.com`,
      telephone: '+223 76 11 11 11',
    },
  })
  expect(tuteur.status()).toBe(201)

  const eleve = await api.post('/api/eleves/', {
    data: {
      nom: 'NoteEleve', prenom: `Notes${Date.now()}`, date_de_naissance: '2010-01-01',
      lieu_de_naissance: 'Bamako', sexe: 'F', statut: 'actif',
      tuteur_id: (await tuteur.json()).id,
    },
  })
  expect(eleve.status()).toBe(201)
  const matriculeEleve = (await eleve.json()).matricule

  const annees = await (await api.get('/api/anneesScolaires/')).json()
  const anneeActive = (Array.isArray(annees) ? annees : annees.items).find((a: { active: boolean }) => a.active)
  const insc = await api.post('/api/inscriptions/', {
    data: {
      matricule_eleve: matriculeEleve, id_classe: classeId, id_annee_scolaire: anneeActive.id,
    },
  })
  expect(insc.status()).toBe(201)

  return { classeId, coursId, classeNom, coursNom }
}

async function nettoyer(api: APIRequestContext, anneeId: number, trimestreId: number) {
  if (!anneeId && !trimestreId) return
  const notes = await (await api.get('/api/notes/', { params: { id_trimestre: trimestreId, limit: 500 } })).json()
  for (const n of notes) await api.delete(`/api/notes/${n.id}`)
  if (trimestreId) await api.delete(`/api/trimestres/${trimestreId}`)
  if (anneeId) await api.delete(`/api/anneesScolaires/${anneeId}`)
}

test.describe('Saisie des notes', () => {
  test('une nouvelle année est directement saisissable (périodes auto-générées)', async ({ page }) => {
    const api = await creerApiContexte()
    let anneeId = 0
    let trimestreId = 0
    try {
      const created = await creerAnnee(api)
      anneeId = created.anneeId
      trimestreId = created.trimestreId
      const { classeId, coursId, classeNom, coursNom } = await creerFixtures(api)

      await login(page, 'admin')
      await page.goto('/app/notes')
      await expect(page.getByRole('heading', { name: 'Saisie des notes' })).toBeVisible()

      await page.getByLabel('Année scolaire').selectOption({ label: `${PREFIX} — Année` })

      await expect(page.getByLabel('Période')).toBeDisabled()
      await expect(page.getByLabel('Matière')).toBeDisabled()

      await page.getByLabel('Classe').selectOption({ label: classeNom })

      const periode = page.getByLabel('Période')
      await expect(periode.locator('option[value="' + trimestreId + '"]')).toHaveCount(1, { timeout: 10_000 })
      await periode.selectOption(String(trimestreId))

      const matiere = page.getByLabel('Matière')
      await expect(matiere.locator('option').filter({ hasText: coursNom })).toHaveCount(1, { timeout: 10_000 })
      await matiere.selectOption({ label: coursNom })

      const inputs = page.locator('input[aria-label^="Note de"]')
      await expect(inputs.first()).toBeVisible({ timeout: 10_000 })
      const nbEleves = await inputs.count()
      expect(nbEleves).toBeGreaterThan(0)

      await inputs.first().fill('7.5')
      await expect(page.locator('tbody tr').first()).toContainText('Nouveau')

      await page.getByRole('button', { name: 'Enregistrer' }).click()
      await expect(page.getByRole('status')).toContainText('Notes enregistrées.', { timeout: 10_000 })
      await expect(page.locator('tbody tr').first()).toContainText('Enregistré')

      let notes = await (
        await api.get('/api/notes/', { params: { id_classe: classeId, id_cours: coursId, id_trimestre: trimestreId } })
      ).json()
      expect(notes).toHaveLength(1)
      expect(notes[0].note).toBe(7.5)

      await inputs.first().fill('9')
      await expect(page.locator('tbody tr').first()).toContainText('Modifié')

      await page.getByRole('button', { name: 'Enregistrer' }).click()
      await expect(page.getByRole('status')).toContainText('Notes enregistrées.', { timeout: 10_000 })

      notes = await (
        await api.get('/api/notes/', { params: { id_classe: classeId, id_cours: coursId, id_trimestre: trimestreId } })
      ).json()
      expect(notes).toHaveLength(1)
      expect(notes[0].note).toBe(9)
    } finally {
      await nettoyer(api, anneeId, trimestreId)
      await api.dispose()
    }
  })

  test("année sans trimestre : message explicite au lieu d'une page vide", async ({ page }) => {
    const api = await creerApiContexte()
    let anneeId = 0
    try {
      const { classeNom } = await creerFixtures(api)
      const anneeRes = await api.post('/api/anneesScolaires/', {
        data: { libelle: `${PREFIX} — Sans période`, date_debut: '2026-01-05', date_fin: '2026-12-20', active: false },
      })
      expect(anneeRes.ok(), `création année (${anneeRes.status()}): ${await anneeRes.text()}`).toBeTruthy()
      anneeId = (await anneeRes.json()).id

      const trimestres = await (
        await api.get('/api/trimestres/', { params: { annee_scolaire_id: anneeId, limit: 500 } })
      ).json()
      for (const t of trimestres) await api.delete(`/api/trimestres/${t.id}`)

      await login(page, 'admin')
      await page.goto('/app/notes')
      await page.getByLabel('Année scolaire').selectOption({ label: `${PREFIX} — Sans période` })
      await page.getByLabel('Classe').selectOption({ label: classeNom })

      await expect(page.getByText('Aucune période pour cette année')).toBeVisible({ timeout: 10_000 })
    } finally {
      if (anneeId) await api.delete(`/api/anneesScolaires/${anneeId}`)
      await api.dispose()
    }
  })
})
