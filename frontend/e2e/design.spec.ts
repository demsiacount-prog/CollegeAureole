import { test, expect } from '@playwright/test'
import { login } from './helpers'

const HALO = '217, 167, 92' // #d9a75c
const BRAND = 'rgb(45, 110, 232)' // #2d6ee8

test.describe('Design system v3 — halo réservé (focus + sidebar + marque), actions primaires en brand', () => {
  test('page de connexion : marque en halo, actions/boutons en brand', async ({ page }) => {
    await page.goto('/connexion')

    const marque = page.getByText('Collège Auréole').first()
    await expect(marque).toBeVisible()
    const marqueColor = await marque.evaluate((el) => getComputedStyle(el).color)
    expect(marqueColor, 'titre de marque = halo').toBe(`rgb(${HALO})`)

    const boutonConnexion = page.getByRole('button', { name: 'Se connecter' })
    await expect(boutonConnexion).toHaveCSS('background-color', BRAND)

    const cadenas = page.locator('svg.lucide-lock-keyhole')
    const cadenasBox = await cadenas.evaluate((el) => {
      const parent = el.closest('div')
      return parent ? getComputedStyle(parent).backgroundColor : ''
    })
    expect(cadenasBox, 'carré cadenas = brand').toBe(BRAND)
  })

  test('focus clavier : anneau halo sur les champs (focus réservé au halo)', async ({ page }) => {
    await page.goto('/connexion')
    const email = page.getByPlaceholder('prenom.nom@etablissement.com')
    await email.focus()
    await page.waitForTimeout(150)
    const shadow = await email.evaluate((el) => getComputedStyle(el).boxShadow)
    expect(shadow, `box-shadow du focus = halo. Obtenu : ${shadow}`).toContain(HALO)
  })

  test('après connexion : item actif de la sidebar en halo, bouton primaire et contenu en brand', async ({ page }) => {
    await login(page, 'admin')
    await page.goto('/app/salles')

    const actif = page.locator('a[href="/app/salles"]')
    await expect(actif).toBeVisible()
    const bgActif = await actif.evaluate((el) => getComputedStyle(el).backgroundColor)
    expect(bgActif, 'fond item actif = halo-wash').toContain(HALO)
    await expect(actif.locator('> span').first()).toHaveCSS('background-color', `rgb(${HALO})`, {
      timeout: 5_000,
    })

    const boutonPrimaire = page.getByRole('button', { name: 'Nouvelle salle' })
    await expect(boutonPrimaire).toHaveCSS('background-color', BRAND)

    const haloEnContexte = await page.evaluate(() => {
      const main = document.querySelector('main')
      if (!main) return []
      const out: string[] = []
      for (const el of main.querySelectorAll<HTMLElement>('*')) {
        const style = getComputedStyle(el)
        const bg = style.backgroundColor
        const color = style.color
        const border = style.borderColor
        if (
          bg === 'rgb(217, 167, 92)' ||
          color === 'rgb(217, 167, 92)' ||
          border === 'rgb(217, 167, 92)'
        ) {
          out.push(`${el.tagName}.${el.className}`.slice(0, 80))
        }
      }
      return out
    })
    expect(haloEnContexte, 'aucun halo décoratif dans le contenu principal').toEqual([])
  })
})
