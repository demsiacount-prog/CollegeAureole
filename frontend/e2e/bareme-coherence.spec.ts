import { test, expect, request, type APIRequestContext } from '@playwright/test'
import { baremeNiveau, appreciation } from '../src/lib/bareme'

const BASE_URL = 'http://localhost:3001'

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

test('les appréciations stockées par le backend suivent la règle frontend (EF1)', async () => {
  const api = await creerApiContexte()
  try {
    const classes = await (await api.get('/api/classes/')).json()
    const ef1Classes = classes.filter((c: { niveau?: string }) => {
      const n = String(c.niveau ?? '')
      const ordre = parseInt(n, 10)
      return /^\d/.test(n) && /année|annee/i.test(n) && ordre >= 1 && ordre <= 6
    })
    expect(ef1Classes.length, 'aucune classe EF1 trouvée').toBeGreaterThan(0)

    let checks = 0
    for (const ef1 of ef1Classes) {
      const bareme = baremeNiveau(ef1.niveau)
      const res = await api.get('/api/bulletins/', { params: { id_classe: ef1.id, limit: 500 } })
      const bulletins = await res.json()
      for (const b of bulletins) {
        const attendue = appreciation(b.moyenne_generale, bareme)
        expect(
          b.appreciation,
          `bulletin ${b.matricule_eleve} (${ef1.niveau}) : moyenne ${b.moyenne_generale}/${bareme}`,
        ).toBe(attendue)
        checks++
      }
    }
    expect(checks, 'aucun bulletin EF1 à vérifier').toBeGreaterThan(0)
  } finally {
    await api.dispose()
  }
})
