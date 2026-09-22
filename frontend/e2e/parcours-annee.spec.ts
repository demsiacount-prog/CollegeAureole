import { test, expect, type Page } from '@playwright/test'
import { login, apiContext } from './helpers'

const NOM_ELEVE = 'E2E'
const PRENOM_ELEVE = 'Parcours'
const NOM_TUTEUR = 'E2E'
const PRENOM_TUTEUR = 'Tuteur'
const NOM_ENSEIGNANT = 'E2E'
const PRENOM_ENSEIGNANT = 'Enseignant'
const NIVEAU_CLASSE = '6ème Année'
const NOM_CLASSE = 'E2E'
const LIBELLE_CLASSE = `${NIVEAU_CLASSE} — ${NOM_CLASSE}`
const NOM_SALLE = 'Salle E2E'
const ROW_REF = new RegExp(`${PRENOM_ELEVE}\\s+${NOM_ELEVE}|${NOM_ELEVE}\\s+${PRENOM_ELEVE}`)
const NOM_COURS = 'E2E Matière'
const FRAIS_INSCRIPTION = '8000'
const MENSUALITE = '5000'
const NOTE = '8'

function escapeRegExp(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

async function pickCombobox(page: Page, value: string) {
  const combobox = page.getByRole('combobox').first()
  await combobox.click()
  await combobox.fill(value)
  await page.getByRole('option', { name: new RegExp(escapeRegExp(value)) }).first().click()
}

  test.describe('Parcours complet de l\'année scolaire (base unique collegeaureole, 3001)', () => {
  test('création des entités pédagogiques via l\'UI (salle, enseignant, classe, cours)', async ({ page }) => {
    await login(page)

    await page.goto('/app/salles')
    await page.getByRole('button', { name: 'Nouvelle salle' }).click()
    await page.getByLabel('Nom', { exact: true }).fill(NOM_SALLE)
    await page.getByRole('button', { name: 'Créer' }).click()
    await expect(page.getByText('Salle créée')).toBeVisible({ timeout: 10_000 })
    await page.getByLabel('Rechercher une salle').fill(NOM_SALLE)
    await expect(page.locator('tbody tr', { hasText: NOM_SALLE })).toBeVisible()

    await page.goto('/app/enseignants')
    await page.getByRole('button', { name: 'Nouvel enseignant' }).click()
    await page.getByLabel('Prénom', { exact: true }).fill(PRENOM_ENSEIGNANT)
    await page.getByLabel('Nom', { exact: true }).fill(NOM_ENSEIGNANT)
    await page.getByLabel('Spécialité').fill('Pédagogie générale')
    await page.getByLabel('E-mail').fill('e2e.enseignant@etablissement.com')
    await page.getByLabel('Téléphone').fill('+223 76 11 22 33')
    await page.getByLabel('Adresse', { exact: true }).fill('Badalabougou, Bamako')
    await page.getByRole('button', { name: 'Créer' }).click()
    await expect(page.getByText('Enseignant créé.')).toBeVisible({ timeout: 10_000 })
    await page.getByLabel('Rechercher un enseignant').fill(NOM_ENSEIGNANT)
    await expect(page.locator('tbody tr', { hasText: 'Enseignant E2E' })).toBeVisible({ timeout: 10_000 })

    await page.goto('/app/classes')
    await page.getByRole('button', { name: 'Nouvelle classe' }).click()
    await page.getByLabel('Nom de la classe').fill(NOM_CLASSE)
    await page.getByLabel('Niveau', { exact: true }).selectOption(NIVEAU_CLASSE)
    await page.getByLabel('Salle').selectOption({ label: NOM_SALLE })
    await page.getByLabel('Frais d\'inscription (FCFA)').fill(FRAIS_INSCRIPTION)
    await page.getByLabel('Mensualité (FCFA)').fill(MENSUALITE)
    await page.getByRole('button', { name: 'Créer' }).click()
    await expect(page.getByText('Classe créée.')).toBeVisible({ timeout: 10_000 })
    const classeRow = page.locator('tbody tr', { hasText: NOM_CLASSE })
    await expect(classeRow).toBeVisible()
    await expect(classeRow).toContainText('6ème Année')
    await expect(classeRow).toContainText('8 000 FCFA')
    await expect(classeRow).toContainText('5 000 FCFA')

    await page.goto('/app/cours')
    await page.getByRole('button', { name: 'Nouveau cours' }).click()
    await page.getByLabel('Nom', { exact: true }).fill(NOM_COURS)
    await page.getByLabel('Description').fill('Matière créée pour le parcours e2e')
    await page.getByLabel('Volume horaire (h)').fill('3')
    await pickCombobox(page, `${PRENOM_ENSEIGNANT} ${NOM_ENSEIGNANT}`)
    const classeCheckboxRow = page.getByText(LIBELLE_CLASSE, { exact: true }).locator('xpath=ancestor::div[1]')
    await classeCheckboxRow.getByRole('checkbox').check()
    await page.getByRole('button', { name: 'Créer' }).click()
    await expect(page.getByText('Cours créé avec succès')).toBeVisible({ timeout: 10_000 })

    const api = await apiContext()
    const cours = await (await api.get('/api/cours/', { params: { limit: 500 } })).json()
    const monCours = cours.find((c) => c.nom === NOM_COURS)
    expect(monCours).toBeTruthy()
    expect(monCours.matricule_enseignant).toBeTruthy()
    expect(monCours.coefficients?.length ?? 0).toBeGreaterThan(0)
    await api.dispose()
  })

  test('inscription complète via l\'assistant puis paiement via l\'UI', async ({ page }) => {
    await login(page)

    await page.goto('/app/inscriptions')
    await page.getByRole('button', { name: 'Nouvelle inscription' }).first().click()

    await expect(page.getByText('Nouvelle inscription').first()).toBeVisible()
    await expect(page.getByText("Identité de l'élève").first()).toBeVisible()

    await page.getByLabel('Nom', { exact: true }).fill(NOM_ELEVE)
    await page.getByLabel('Prénom', { exact: true }).fill(PRENOM_ELEVE)
    await page.getByLabel('Date de naissance').fill('2014-04-12')
    await page.getByLabel('Lieu de naissance').fill('Bamako')
    await page.getByRole('button', { name: 'Suivant' }).click()

    await page.getByLabel('Nom du tuteur', { exact: true }).fill(NOM_TUTEUR)
    await page.getByLabel('Prénom du tuteur', { exact: true }).fill(PRENOM_TUTEUR)
    await page.getByLabel('Email', { exact: true }).fill('e2e.tuteur@etablissement.com')
    await page.getByLabel('Téléphone', { exact: true }).fill('+223 76 44 55 66')
    await page.getByLabel('Adresse', { exact: true }).fill('Badalabougou, Bamako')
    await page.getByLabel('Profession', { exact: true }).fill('Commerçant')
    await page.getByRole('button', { name: 'Suivant' }).click()

    await page.getByLabel('Niveau demandé').selectOption(NIVEAU_CLASSE)
    await page.getByLabel('Classe attribuée').selectOption({ label: LIBELLE_CLASSE })
    await page.getByRole('button', { name: 'Suivant' }).click()

    // L'état civil est requis pour marquer l'acte de naissance comme reçu.
    await page.getByLabel('Acte de naissance N°').fill('N° 1234/25')
    await page.getByLabel("Date de l'acte").fill('2012-06-15')
    await page.getByLabel('Délivré par').fill('Mairie de Bamako')

    const marquerRecu = page.getByRole('button', { name: 'Marquer reçu' })
    await marquerRecu.first().click()
    await expect(marquerRecu).toHaveCount(1)
    await marquerRecu.first().click()
    await page.getByRole('button', { name: 'Suivant' }).click()

    await expect(page.getByText(`${PRENOM_ELEVE} ${NOM_ELEVE}`).first()).toBeVisible()
    await page.getByRole('button', { name: "Enregistrer l'inscription" }).click()
    await expect(page.getByText('Inscription enregistrée.')).toBeVisible({ timeout: 30_000 })

    await expect(page.getByLabel('Rechercher une inscription')).toBeVisible({ timeout: 15_000 })
    await page.getByLabel('Rechercher une inscription').fill(NOM_ELEVE)
    const row = page.locator('tbody tr', { hasText: ROW_REF })
    await expect(row).toBeVisible({ timeout: 15_000 })
    await expect(row).toContainText('Inscrit')

    const api = await apiContext()
    const inscriptions = await (await api.get('/api/inscriptions/', { params: { q: NOM_ELEVE } })).json()
    const insc = inscriptions[0]
    expect(insc).toBeTruthy()
    expect(insc.statut).toBe('Inscrit')
    const matricule = insc.matricule_eleve
    expect(matricule).toMatch(/^AU25\d+/)
    await api.dispose()

    await page.goto('/app/paiements')
    await page.getByRole('button', { name: 'Nouveau paiement' }).click()
    await pickCombobox(page, `${NOM_ELEVE} ${PRENOM_ELEVE}`)
    const echRow = page.locator('div.flex.items-center.gap-3', { hasText: 'Inscription' }).first()
    await echRow.getByRole('checkbox').check()
    await page.getByLabel('Montant (FCFA)').fill(FRAIS_INSCRIPTION)
    await page.getByLabel('Mode de paiement').selectOption('ESPECES')
    await page.getByRole('button', { name: 'Enregistrer' }).click()
    await expect(page.getByText(/Paiement enregistré/)).toBeVisible({ timeout: 15_000 })

    await page.getByLabel('Rechercher un paiement').fill(NOM_ELEVE)
    const paiementRow = page.locator('tbody tr', { hasText: ROW_REF })
    await expect(paiementRow).toBeVisible({ timeout: 15_000 })
    await expect(paiementRow).toContainText('PAI')
    await expect(paiementRow).toContainText('ESPECES')
    await expect(paiementRow).toContainText('8 000')

    expect(matricule).toBeTruthy()
  })

  test('saisie de note via l\'UI puis génération et publication du bulletin', async ({ page }) => {
    await login(page)

    const api = await apiContext()
    const inscriptions = await (await api.get('/api/inscriptions/', { params: { q: NOM_ELEVE } })).json()
    const matricule = inscriptions[0]?.matricule_eleve
    expect(matricule).toBeTruthy()
    const cours = await (await api.get('/api/cours/', { params: { limit: 500 } })).json()
    const coursId = cours.find((c) => c.nom === NOM_COURS)?.id
    expect(coursId).toBeTruthy()
    await api.dispose()

    await page.goto('/app/notes')
    await page.getByLabel('Classe').selectOption({ label: LIBELLE_CLASSE })
    const periode = page.getByLabel('Période')
    await expect(periode).toBeEnabled({ timeout: 15_000 })
    await periode.selectOption({ index: 1 })
    const matiere = page.getByLabel('Matière')
    await expect(matiere).toBeEnabled({ timeout: 10_000 })
    await matiere.selectOption({ label: NOM_COURS })

    const noteInput = page.getByLabel(`Note de composition de ${PRENOM_ELEVE} ${NOM_ELEVE}`)
    await expect(noteInput).toBeVisible({ timeout: 15_000 })
    await noteInput.fill(NOTE)

    // Perte de focus : l'auto-enregistrement (onBlur) sauvegarde la note.
    await page.getByRole('heading', { name: 'Saisie des notes' }).click()
    await expect(page.locator('tbody tr', { hasText: ROW_REF })).toContainText('Enregistré', { timeout: 15_000 })

    // La sauvegarde manuelle reste actionnable et confirme.
    await page.getByRole('button', { name: 'Enregistrer' }).click()
    await expect(page.getByText('Notes enregistrées.')).toBeVisible({ timeout: 15_000 })

    await page.goto('/app/bulletins')
    await page.getByLabel('Classe').selectOption({ label: LIBELLE_CLASSE })
    const bulletinPeriode = page.getByLabel('Période')
    await expect(bulletinPeriode).toBeEnabled({ timeout: 15_000 })
    await bulletinPeriode.selectOption({ index: 1 })
    await page.getByRole('button', { name: 'Générer pour la classe' }).click()
    await expect(page.getByText('1 bulletin(s) généré(s)')).toBeVisible({ timeout: 20_000 })
    const bulRow = page.locator('tbody tr', { hasText: ROW_REF })
    await expect(bulRow).toBeVisible({ timeout: 15_000 })
    await expect(bulRow).toContainText('8.00 / 10')
    await expect(bulRow).toContainText('Très bien')
    await expect(bulRow).toContainText('Brouillon')

    // Le rang n'est affiché qu'après publication (rangs calculés à la publication).
    await page.getByRole('button', { name: 'Publier', exact: true }).click()
    await expect(page.getByText('1 bulletin(s) publié(s)')).toBeVisible({ timeout: 15_000 })
    await expect(bulRow).toContainText('Publié', { timeout: 15_000 })
    await expect(bulRow).toContainText('1er', { timeout: 15_000 })
  })

  test('consultation du dossier élève : profil, résultats et bulletin', async ({ page }) => {
    await login(page)

    const api = await apiContext()
    const inscriptions = await (await api.get('/api/inscriptions/', { params: { q: NOM_ELEVE } })).json()
    const matricule = inscriptions[0]?.matricule_eleve
    expect(matricule).toBeTruthy()
    await api.dispose()

    await page.goto(`/app/eleves/${matricule}`)
    await expect(page.getByRole('heading', { name: `${PRENOM_ELEVE} ${NOM_ELEVE}` })).toBeVisible()
    await expect(page.getByText(LIBELLE_CLASSE).first()).toBeVisible()
    await expect(page.getByText(matricule).first()).toBeVisible()

    await page.getByRole('tab', { name: 'Bulletins' }).click()
    const bulDossier = page.locator('tbody tr', { hasText: 'Trimestre 1' })
    await expect(bulDossier).toBeVisible({ timeout: 10_000 })
    await expect(bulDossier).toContainText('8.00')
    await expect(bulDossier).toContainText('1ᵉ', { timeout: 10_000 })
    await expect(bulDossier).toContainText('Publié', { timeout: 10_000 })
  })

  test('nettoyage des données du parcours via l\'API', async () => {
    const api = await apiContext()

    const inscriptions = await (await api.get('/api/inscriptions/', { params: { q: NOM_ELEVE } })).json()
    for (const insc of inscriptions) {
      const paiements = await (
        await api.get('/api/paiements/', { params: { id_inscription: insc.id, limit: 500 } })
      ).json()
      for (const p of paiements) {
        const del = await api.delete(`/api/paiements/${p.id}`)
        expect(del.ok()).toBeTruthy()
      }
      const res = await api.delete(`/api/inscriptions/${insc.id}`)
      expect(res.ok()).toBeTruthy()
    }

    const cours = await (await api.get('/api/cours/', { params: { limit: 500 } })).json()
    const monCours = cours.find((c) => c.nom === NOM_COURS)
    if (monCours) await api.delete(`/api/cours/${monCours.id}`)

    const classes = await (await api.get('/api/classes/', { params: { limit: 500 } })).json()
    const maClasse = classes.find((c) => c.nom === NOM_CLASSE)
    if (maClasse) await api.delete(`/api/classes/${maClasse.id}`)

    const enseignants = await (await api.get('/api/enseignants/', { params: { limit: 500 } })).json()
    const monEnseignant = enseignants.find((e) => e.nom === NOM_ENSEIGNANT)
    if (monEnseignant) await api.delete(`/api/enseignants/${monEnseignant.matricule}`)

    const salles = await (await api.get('/api/salles/', { params: { limit: 500 } })).json()
    const maSalle = salles.find((s) => s.nom === NOM_SALLE)
    if (maSalle) await api.delete(`/api/salles/${maSalle.id}`)

    const apres = await (await api.get('/api/inscriptions/', { params: { q: NOM_ELEVE } })).json()
    expect(apres.length).toBe(0)
    await api.dispose()
  })
})
