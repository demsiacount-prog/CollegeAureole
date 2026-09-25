import { describe, expect, it } from 'vitest'
import { estNiveauJardin, NIVEAUX_CLASSES, NIVEAUX_FONDAMENTAL, NIVEAUX_JARDIN, niveauOrdre } from './niveaux'

describe('NIVEAUX_CLASSES', () => {
  it('concatène jardin puis fondamental, sans doublon ni omission', () => {
    expect(NIVEAUX_CLASSES).toHaveLength(NIVEAUX_JARDIN.length + NIVEAUX_FONDAMENTAL.length)
    expect(new Set(NIVEAUX_CLASSES).size).toBe(NIVEAUX_CLASSES.length)
  })

  it('le fondamental va bien de la 1ère à la 9ème Année, dans l’ordre', () => {
    expect(NIVEAUX_FONDAMENTAL).toEqual([
      '1ère Année', '2ème Année', '3ème Année',
      '4ème Année', '5ème Année', '6ème Année',
      '7ème Année', '8ème Année', '9ème Année',
    ])
  })
})

describe('estNiveauJardin', () => {
  it.each(NIVEAUX_JARDIN)('"%s" est un niveau jardin', (niveau) => {
    expect(estNiveauJardin(niveau)).toBe(true)
  })

  it.each(NIVEAUX_FONDAMENTAL)('"%s" n’est pas un niveau jardin', (niveau) => {
    expect(estNiveauJardin(niveau)).toBe(false)
  })

  it('tolère les espaces superflus mais pas une casse différente (correspondance exacte)', () => {
    expect(estNiveauJardin('  Petite Section  ')).toBe(true)
    expect(estNiveauJardin('petite section')).toBe(false)
  })

  it('gère les valeurs absentes sans lever d’exception', () => {
    expect(estNiveauJardin(null)).toBe(false)
    expect(estNiveauJardin(undefined)).toBe(false)
  })
})

describe('niveauOrdre', () => {
  it('extrait le rang numérique en tête du libellé', () => {
    expect(niveauOrdre('1ère Année')).toBe(1)
    expect(niveauOrdre('9ème Année')).toBe(9)
  })

  it('retourne null pour un niveau non numérique (classes de jardin)', () => {
    expect(niveauOrdre('Petite Section')).toBeNull()
    expect(niveauOrdre(null)).toBeNull()
    expect(niveauOrdre(undefined)).toBeNull()
  })
})
