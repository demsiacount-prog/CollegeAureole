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

test('les appréciations backend suivent la règle frontend pour les classes existantes', async () => {
  const api = await creerApiContexte()
  try {
    const classes = await (await api.get('/api/classes/')).json()
    const classeList = Array.isArray(classes) ? classes : classes.items
    if (classeList.length === 0) return

    let checks = 0
    for (const cls of classeList) {
      const bareme = baremeNiveau(cls.niveau)
      const res = await api.get('/api/bulletins/', { params: { id_classe: cls.id, limit: 500 } })
      const bulletins = await res.json()
      for (const b of bulletins) {
        const attendue = appreciation(b.moyenne_generale, bareme)
        expect(
          b.appreciation,
          `bulletin ${b.matricule_eleve} (${cls.niveau}) : moyenne ${b.moyenne_generale}/${bareme}`,
        ).toBe(attendue)
        checks++
      }
    }
  } finally {
    await api.dispose()
  }
})
