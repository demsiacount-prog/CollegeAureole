import { test, expect, request, type APIRequestContext } from '@playwright/test'
import { login } from './helpers'

const BASE_URL = 'http://localhost:3001'
const PREFIX = `PERIODES E2E ${Date.now()}`

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

test('bouton « Générer les périodes par défaut » dans Paramètres', async ({ page }) => {
  const api = await creerApiContexte()
  let anneeId = 0
  try {
    const anneeRes = await api.post('/api/anneesScolaires/', {
      data: { libelle: PREFIX, date_debut: '2026-10-01', date_fin: '2027-07-10', active: false },
    })
    expect(anneeRes.ok(), `création année (${anneeRes.status()}): ${await anneeRes.text()}`).toBeTruthy()
    anneeId = (await anneeRes.json()).id

    const trimestres = await (
      await api.get('/api/trimestres/', { params: { annee_scolaire_id: anneeId, limit: 500 } })
    ).json()
    for (const t of trimestres) await api.delete(`/api/trimestres/${t.id}`)

    await login(page, 'admin')
    await page.goto('/app/parametres')

    const ligne = page.getByRole('row').filter({ hasText: PREFIX })
    await expect(ligne).toBeVisible()
    await ligne.getByRole('button', { name: /Générer les périodes par défaut/ }).click()

    await expect(page.getByRole('status')).toContainText('12 périodes générées', { timeout: 10_000 })

    const regeneres = await (
      await api.get('/api/trimestres/', { params: { annee_scolaire_id: anneeId, limit: 500 } })
    ).json()
    expect(regeneres).toHaveLength(12)
    expect(regeneres.some((t: { type: string }) => t.type === 'COMPOSITION')).toBeTruthy()
    expect(regeneres.some((t: { type: string }) => t.type === 'TRIMESTRE')).toBeTruthy()
  } finally {
    if (anneeId) await api.delete(`/api/anneesScolaires/${anneeId}`)
    await api.dispose()
  }
})
