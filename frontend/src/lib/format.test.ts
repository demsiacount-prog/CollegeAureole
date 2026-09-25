import { describe, expect, it } from 'vitest'
import { formatDate, formatMontant, formatMoyenne } from './format'

describe('formatDate', () => {
  it('retourne un tiret cadratin pour une valeur absente', () => {
    expect(formatDate(null)).toBe('—')
    expect(formatDate(undefined)).toBe('—')
    expect(formatDate('')).toBe('—')
  })

  it('formate une date ISO en date lisible (jour, mois abrégé, année)', () => {
    const resultat = formatDate('2030-09-15')
    expect(resultat).not.toBe('2030-09-15')
    expect(resultat).toContain('2030')
    expect(resultat).toMatch(/15/)
  })

  it('renvoie la valeur telle quelle si elle est illisible comme date', () => {
    expect(formatDate('pas-une-date')).toBe('pas-une-date')
  })
})

describe('formatMontant', () => {
  it('retourne un tiret cadratin pour null/undefined (mais pas pour 0)', () => {
    expect(formatMontant(null)).toBe('—')
    expect(formatMontant(undefined)).toBe('—')
    expect(formatMontant(0)).not.toBe('—')
  })

  it('formate un nombre sans décimales (le Franc CFA n’a pas de sous-unité usuelle)', () => {
    const resultat = formatMontant(15000)
    expect(resultat).not.toContain('.')
    expect(resultat.replace(/[^\d]/g, '')).toBe('15000')
  })

  it('un montant plus élevé produit une chaîne différente', () => {
    expect(formatMontant(1000)).not.toBe(formatMontant(2000))
  })
})

describe('formatMoyenne', () => {
  it('retourne un tiret cadratin pour null/undefined, jamais pour 0', () => {
    expect(formatMoyenne(null, 20)).toBe('—')
    expect(formatMoyenne(undefined, 20)).toBe('—')
    expect(formatMoyenne(0, 20)).toBe('0.00 / 20')
  })

  it('affiche toujours le barème fourni, jamais un défaut implicite', () => {
    expect(formatMoyenne(8.5, 10)).toBe('8.50 / 10')
    expect(formatMoyenne(15, 20)).toBe('15.00 / 20')
  })

  it('arrondit l’affichage à deux décimales', () => {
    expect(formatMoyenne(13.456, 20)).toBe('13.46 / 20')
  })
})
