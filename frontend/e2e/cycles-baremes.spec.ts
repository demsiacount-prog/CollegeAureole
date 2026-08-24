import { test, expect } from '@playwright/test'
import { login } from './helpers'

// Règle métier :
// - EF1 (1ère–6ème Année) : notes /10, moyenne SIMPLE, aucun coefficient ;
// - EF2 (7ème–9ème Année) : notes /20, moyenne pondérée, « Note × Coefficient ».
const API_BASE = 'http://localhost:3001'

type Auth = { headers: Record<string, string> }

async function authDe(page: import('@playwright/test').Page): Promise<Auth> {
  await login(page, 'admin')
  const token = await page.evaluate(() => localStorage.getItem('aureole_token'))
  return { headers: { Authorization: `Bearer ${token}` } }
}

test.describe('Barèmes et coefficients par cycle', () => {
  test('EF2 : bulletin pondéré avec colonne Note × Coefficient', async ({ page, request }) => {
    const auth = await authDe(page)
    const post = async (url: string, data: unknown) =>
      request.post(`${API_BASE}${url}`, { data, headers: auth.headers })

    let idClasse: number | null = null
    let matriculeEleve: string | null = null
    const nettoyer = async () => {
      try {
        if (matriculeEleve) {
          const inscriptions = await (await request.get(`${API_BASE}/api/inscriptions/`, auth)).json()
          const inscId = inscriptions.find((i: { matricule_eleve: string }) => i.matricule_eleve === matriculeEleve)?.id
          if (inscId != null) await request.delete(`${API_BASE}/api/inscriptions/${inscId}`, { headers: auth.headers })
        }
        if (idClasse != null) await request.delete(`${API_BASE}/api/classes/${idClasse}`, { headers: auth.headers })
      } catch {
        // Le nettoyage ne doit jamais masquer l'échec du test.
      }
    }

    try {
      // Fixtures : enseignant, classe 7ème (EF2), deux cours coef 4 et 2.
      const ens = await post('/api/enseignants/', {
        nom: 'Cyclo', prenom: 'ProfBar', email: 'prof.cyclo@etablissement.com',
        telephone: '+223 76 44 55 66', adresse: 'Bamako', specialite: 'Sciences',
      })
      expect(ens.status()).toBe(201)
      const matriculeEns = (await ens.json()).matricule

      const classe = await post('/api/classes/', { niveau: '7ème Année', nom: 'CycBar' })
      expect(classe.status()).toBe(201)
      idClasse = (await classe.json()).id

      const creerCours = async (nom: string, coefficient: number) => {
        const rep = await post('/api/cours/', {
          nom, description: '', volume_horaire: 2,
          matricule_enseignant: matriculeEns,
          affectations: [{ id_classe: idClasse, coefficient }],
        })
        expect(rep.status()).toBe(201)
        return (await rep.json()).id as number
      }
      const idCoursA = await creerCours('Bar Maths — 7ème', 4)
      const idCoursB = await creerCours('Bar Français — 7ème', 2)

      // Élève inscrit dans la classe.
      const tuteur = await post('/api/tuteurs/', {
        nom: 'Cyclo', prenom: 'TuteurBar', email: 'tuteur.cyclo@etablissement.com',
        telephone: '+223 76 77 88 99',
      })
      expect(tuteur.status()).toBe(201)
      const eleve = await post('/api/eleves/', {
        nom: 'Ponderee', prenom: 'EleveBar', date_de_naissance: '2009-03-03',
        lieu_de_naissance: 'Bamako', sexe: 'M', statut: 'actif',
        tuteur_id: (await tuteur.json()).id,
      })
      expect(eleve.status()).toBe(201)
      matriculeEleve = (await eleve.json()).matricule
      const annees = await (await request.get(`${API_BASE}/api/anneesScolaires/`, auth)).json()
      const anneeActive = annees.find((a: { active: boolean }) => a.active)
      const insc = await post('/api/inscriptions/', {
        matricule_eleve: matriculeEleve, id_classe: idClasse, id_annee_scolaire: anneeActive.id,
      })
      expect(insc.status()).toBe(201)

      // Période TRIMESTRE du second cycle + notes /20.
      const periodes = await (await request.get(`${API_BASE}/api/trimestres/`, auth)).json()
      const trimestreEf2 = periodes.find(
        (t: { type: string; annee_scolaire_id: number }) => t.type === 'TRIMESTRE' && t.annee_scolaire_id === anneeActive.id,
      )
      expect(trimestreEf2).toBeTruthy()
      for (const [idCours, note] of [[idCoursA, 12], [idCoursB, 16]] as const) {
        const rep = await post('/api/notes/', {
          note, matricule_eleve: matriculeEleve, id_cours: idCours,
          id_classe: idClasse, matricule_enseignant: matriculeEns, id_trimestre: trimestreEf2.id,
        })
        expect(rep.status()).toBe(201)
      }

      // Bulletin généré : (12×4 + 16×2) / (4+2) = 80/6 ≈ 13.33.
      const gen = await post('/api/bulletins/generer', {
        matricule_eleve: matriculeEleve, id_trimestre: trimestreEf2.id,
      })
      expect(gen.status()).toBe(201)
      const bulletin = await gen.json()
      expect(bulletin.moyenne_generale).toBeCloseTo(13.33, 2)

      // UI : le détail affiche Moyenne brute, Coefficient et Note × Coefficient.
      await page.goto(`/app/bulletins/${bulletin.id}`)
      const main = page.locator('main')
      await expect(main.getByText('Détail par matière')).toBeVisible({ timeout: 15_000 })
      await expect(main.getByRole('columnheader', { name: 'Note × Coefficient' })).toBeVisible()
      await expect(main.getByRole('columnheader', { name: 'Coefficient', exact: true })).toBeVisible()
      const ligneMaths = main.locator('tbody tr', { hasText: 'Bar Maths — 7ème' })
      await expect(ligneMaths).toContainText('12.00 / 20')
      await expect(ligneMaths).toContainText('48.00')
      const ligneFr = main.locator('tbody tr', { hasText: 'Bar Français — 7ème' })
      await expect(ligneFr).toContainText('16.00 / 20')
      await expect(ligneFr).toContainText('32.00')
    } finally {
      await nettoyer()
    }
  })

  test('EF1 : moyenne simple au bulletin, coefficient refusé sur une classe du premier cycle', async ({ page, request }) => {
    const auth = await authDe(page)
    const post = async (url: string, data: unknown) =>
      request.post(`${API_BASE}${url}`, { data, headers: auth.headers })

    let idClasse: number | null = null
    let matriculeEleve: string | null = null
    const nettoyer = async () => {
      try {
        if (matriculeEleve) {
          const inscriptions = await (await request.get(`${API_BASE}/api/inscriptions/`, auth)).json()
          const inscId = inscriptions.find((i: { matricule_eleve: string }) => i.matricule_eleve === matriculeEleve)?.id
          if (inscId != null) await request.delete(`${API_BASE}/api/inscriptions/${inscId}`, { headers: auth.headers })
        }
        if (idClasse != null) await request.delete(`${API_BASE}/api/classes/${idClasse}`, { headers: auth.headers })
      } catch {
        // Le nettoyage ne doit jamais masquer l'échec du test.
      }
    }

    try {
      const ens = await post('/api/enseignants/', {
        nom: 'CycleUn', prenom: 'MaitreBar', email: 'maitre.cyclo@etablissement.com',
        telephone: '+223 76 10 20 30', adresse: 'Bamako', specialite: "Maître d'école (EF1 — polyvalent)",
      })
      expect(ens.status()).toBe(201)
      const matriculeEns = (await ens.json()).matricule

      const classe = await post('/api/classes/', { niveau: '5ème Année', nom: 'SmpBar' })
      expect(classe.status()).toBe(201)
      idClasse = (await classe.json()).id

      // Règle : un coefficient ≠ 1 est refusé sur une classe EF1.
      const refuse = await post('/api/cours/', {
        nom: 'Bar Refus — 5ème', description: '', volume_horaire: 2,
        matricule_enseignant: matriculeEns,
        affectations: [{ id_classe: idClasse, coefficient: 4 }],
      })
      expect(refuse.status()).toBe(422)

      // Deux cours à coefficient 1 (obligatoire en EF1), élève, notes /10.
      const creerCours = async (nom: string) => {
        const rep = await post('/api/cours/', {
          nom, description: '', volume_horaire: 2,
          matricule_enseignant: matriculeEns,
          affectations: [{ id_classe: idClasse, coefficient: 1 }],
        })
        expect(rep.status()).toBe(201)
        return (await rep.json()).id as number
      }
      const idCoursA = await creerCours('Bar Lecture — 5ème')
      const idCoursB = await creerCours('Bar Calcul — 5ème')

      const tuteur = await post('/api/tuteurs/', {
        nom: 'Simple', prenom: 'TuteurBar', email: 'tuteur.simplebar@etablissement.com',
        telephone: '+223 76 13 24 35',
      })
      expect(tuteur.status()).toBe(201)
      const eleve = await post('/api/eleves/', {
        nom: 'Arithmetique', prenom: 'EleveBar', date_de_naissance: '2013-09-09',
        lieu_de_naissance: 'Bamako', sexe: 'F', statut: 'actif',
        tuteur_id: (await tuteur.json()).id,
      })
      expect(eleve.status()).toBe(201)
      matriculeEleve = (await eleve.json()).matricule
      const annees = await (await request.get(`${API_BASE}/api/anneesScolaires/`, auth)).json()
      const anneeActive = annees.find((a: { active: boolean }) => a.active)
      const insc = await post('/api/inscriptions/', {
        matricule_eleve: matriculeEleve, id_classe: idClasse, id_annee_scolaire: anneeActive.id,
      })
      expect(insc.status()).toBe(201)

      const periodes = await (await request.get(`${API_BASE}/api/trimestres/`, auth)).json()
      const composition = periodes.find(
        (t: { type: string; annee_scolaire_id: number }) => t.type === 'COMPOSITION' && t.annee_scolaire_id === anneeActive.id,
      )
      expect(composition).toBeTruthy()
      for (const [idCours, note] of [[idCoursA, 10], [idCoursB, 0]] as const) {
        const rep = await post('/api/notes/', {
          note, matricule_eleve: matriculeEleve, id_cours: idCours,
          id_classe: idClasse, matricule_enseignant: matriculeEns, id_trimestre: composition.id,
        })
        expect(rep.status()).toBe(201)
      }

      // Bulletin EF1 : moyenne simple (10 + 0) / 2 = 5.00 — pas de pondération.
      const gen = await post('/api/bulletins/generer', {
        matricule_eleve: matriculeEleve, id_trimestre: composition.id,
      })
      expect(gen.status()).toBe(201)
      const bulletin = await gen.json()
      expect(bulletin.moyenne_generale).toBe(5.0)

      // UI EF1 : pas de colonne Coefficient, moyennes brutes sur /10.
      await page.goto(`/app/bulletins/${bulletin.id}`)
      const main = page.locator('main')
      await expect(main.getByText('Détail par matière')).toBeVisible({ timeout: 15_000 })
      await expect(main.getByRole('columnheader', { name: 'Note × Coefficient' })).toHaveCount(0)
      await expect(main.getByRole('columnheader', { name: 'Coefficient', exact: true })).toHaveCount(0)
      const ligneLecture = main.locator('tbody tr', { hasText: 'Bar Lecture — 5ème' })
      await expect(ligneLecture).toContainText('10.00 / 10')
      const ligneCalcul = main.locator('tbody tr', { hasText: 'Bar Calcul — 5ème' })
      await expect(ligneCalcul).toContainText('0.00 / 10')
    } finally {
      await nettoyer()
    }
  })
})
