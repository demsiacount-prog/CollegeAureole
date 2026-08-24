import { test, expect, request as apiRequest } from '@playwright/test'

const ADMIN_EMAIL = 'admin@etablissement.com'
const ADMIN_PASSWORD = 'Password123!'
const API_BASE = 'http://localhost:3001'

test('la réinitialisation des données (purge) conserve le compte connecté', async ({ request }) => {
  const auth = await apiRequest.newContext({ baseURL: API_BASE })
  const res = await auth.post('/api/auth/connexion', {
    data: { email: ADMIN_EMAIL, mot_de_passe: ADMIN_PASSWORD },
  })
  if (res.status() !== 200) throw new Error(`Login API échoué (${res.status()}): ${await res.text()}`)
  const token = (await res.json()).access_token

  const purge = await auth.post(`${API_BASE}/api/setup/purge-donnees`, {
    data: { confirm: true },
    headers: { 'X-Confirm': 'PURGE-DONNEES', Authorization: `Bearer ${token}` },
  })
  expect(purge.status()).toBe(200)

  const status = await request.get(`${API_BASE}/api/setup/status`)
  const statusBody = await status.json()
  expect(statusBody.donnees_presentes).toBe(false)

  const login = await request.post(`${API_BASE}/api/auth/connexion`, {
    data: { email: ADMIN_EMAIL, mot_de_passe: ADMIN_PASSWORD },
  })
  expect(login.status()).toBe(200)
})
