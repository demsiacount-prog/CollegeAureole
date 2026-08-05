import { test, expect, request, type APIRequestContext } from '@playwright/test'
import { loginViaApi } from './helpers'

const BASE_URL = 'http://localhost:3000'
const PREFIX = `NOTES E2E ${Date.now()}`

async function creerApiContexte(): Promise<APIRequestContext> {
  const auth = await request.newContext({ baseURL: BASE_URL })
  const res = await auth.post('/api/auth/connexion', {
    data: { email: 'admin@collegeaureole.ml', mot_de_passe: 'Password123!' },
  })
  if (res.status() !== 200) throw new Error(`Login API échoué (${res.status()})`)
  const { access_token } = await res.json()
  await auth.dispose()
  return request.newContext({
    baseURL: BASE_URL,
    extraHTTPHeaders: { Authorization: `Bearer ${access_token}` },
  })
}

async function creerAnnee(api: APIRequestContext): Promise<{ anneeId: number; trimestreId: number }> {
  const anneeRes = await api.post('/api/anneesScolaires/', {
    data: { libelle: `${PREFIX} — Année`, date_debut: '2026-01-05', date_fin: '2026-12-20', active: false },
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

async function trouverClasseEtCours(api: APIRequestContext): Promise<{ classeId: number; coursId: number }> {
  const classes = await (await api.get('/api/classes/')).json()
  const classe = classes.find((c: { niveau: string; nom: string }) => c.niveau === '6ème Année' && c.nom === 'A')
  if (!classe) throw new Error('Classe 6ème Année — A introuvable')
  const detail = await (await api.get(`/api/classes/${classe.id}`)).json()
  const c = detail.cours.find((x: { nom: string }) => x.nom === 'Mathématiques — 6ème Année')
  if (!c) throw new Error('Cours Mathématiques introuvable pour la classe 6ème Année')
  return { classeId: classe.id, coursId: c.id }
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
      const { classeId, coursId } = await trouverClasseEtCours(api)

      await loginViaApi(page, 'admin')
      await page.goto('/app/notes')
      await expect(page.getByRole('heading', { name: 'Saisie des notes' })).toBeVisible()

      await page.getByLabel('Année scolaire').selectOption({ label: `${PREFIX} — Année` })

      await expect(page.getByLabel('Période')).toBeDisabled()
      await expect(page.getByLabel('Matière')).toBeDisabled()

      await page.getByLabel('Classe').selectOption({ label: '6ème Année — A' })

      const periode = page.getByLabel('Période')
      await expect(periode.locator('option[value="' + trimestreId + '"]')).toHaveCount(1, { timeout: 10_000 })
      await periode.selectOption(String(trimestreId))

      const matiere = page.getByLabel('Matière')
      await expect(matiere.locator('option').filter({ hasText: 'Mathématiques' })).toHaveCount(1, { timeout: 10_000 })
      await matiere.selectOption({ label: 'Mathématiques — 6ème Année' })

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
      const anneeRes = await api.post('/api/anneesScolaires/', {
        data: { libelle: `${PREFIX} — Sans période`, date_debut: '2026-01-05', date_fin: '2026-12-20', active: false },
      })
      expect(anneeRes.ok(), `création année (${anneeRes.status()}): ${await anneeRes.text()}`).toBeTruthy()
      anneeId = (await anneeRes.json()).id

      const trimestres = await (
        await api.get('/api/trimestres/', { params: { annee_scolaire_id: anneeId, limit: 500 } })
      ).json()
      for (const t of trimestres) await api.delete(`/api/trimestres/${t.id}`)

      await loginViaApi(page, 'admin')
      await page.goto('/app/notes')
      await page.getByLabel('Année scolaire').selectOption({ label: `${PREFIX} — Sans période` })
      await page.getByLabel('Classe').selectOption({ label: '6ème Année — A' })

      await expect(page.getByText('Aucune période pour cette année')).toBeVisible({ timeout: 10_000 })
    } finally {
      if (anneeId) await api.delete(`/api/anneesScolaires/${anneeId}`)
      await api.dispose()
    }
  })
})
