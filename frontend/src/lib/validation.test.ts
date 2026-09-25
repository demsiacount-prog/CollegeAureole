import { describe, expect, it } from 'vitest'
import {
  dateFinApresDebut,
  email,
  hasErrors,
  heureFinApresDebut,
  minLength,
  minNumber,
  phone,
  positiveNumber,
  required,
  validateFields,
} from './validation'

describe('required', () => {
  it('signale une valeur vide, null, undefined ou faite uniquement d’espaces', () => {
    expect(required('')).toBeDefined()
    expect(required('   ')).toBeDefined()
    expect(required(null)).toBeDefined()
    expect(required(undefined)).toBeDefined()
  })

  it('accepte 0 et false comme valeurs renseignées (pas vides)', () => {
    expect(required(0)).toBeUndefined()
    expect(required(false)).toBeUndefined()
  })

  it('inclut le libellé personnalisé dans le message', () => {
    expect(required('', 'Le nom')).toBe('Le nom est obligatoire.')
  })
})

describe('minNumber / positiveNumber', () => {
  it('minNumber refuse une valeur en dessous du minimum', () => {
    expect(minNumber(4, 5)).toMatch(/au moins 5/)
    expect(minNumber(5, 5)).toBeUndefined()
    expect(minNumber(6, 5)).toBeUndefined()
  })

  it('minNumber convertit les chaînes numériques', () => {
    expect(minNumber('10', 5)).toBeUndefined()
    expect(minNumber('abc', 5)).toMatch(/nombre/)
  })

  it('positiveNumber refuse zéro et les négatifs', () => {
    expect(positiveNumber(0)).toBeDefined()
    expect(positiveNumber(-1)).toBeDefined()
    expect(positiveNumber(1)).toBeUndefined()
  })

  it('positiveNumber et minNumber exigent une valeur (pas de défaut silencieux)', () => {
    expect(positiveNumber('')).toMatch(/obligatoire/)
    expect(minNumber(null, 0)).toMatch(/obligatoire/)
  })
})

describe('email', () => {
  it('accepte un champ vide (optionnel par défaut, cf. required séparé)', () => {
    expect(email('')).toBeUndefined()
    expect(email(undefined)).toBeUndefined()
  })

  it('valide un e-mail correctement formé', () => {
    expect(email('admin@aureole.ml')).toBeUndefined()
  })

  it.each(['pas-un-email', 'a@b', '@aureole.ml', 'a@aureole.', 'a b@aureole.ml'])(
    'rejette "%s"',
    (v) => {
      expect(email(v)).toBeDefined()
    },
  )
})

describe('phone', () => {
  it('accepte un champ vide', () => {
    expect(phone('')).toBeUndefined()
  })

  it('exige au moins 8 chiffres, espaces/tirets/indicatif ignorés', () => {
    expect(phone('+223 20 22 33 44')).toBeUndefined()
    expect(phone('20-22-33')).toBeDefined() // 6 chiffres
    expect(phone('1234567')).toBeDefined() // 7 chiffres
    expect(phone('12345678')).toBeUndefined() // 8 chiffres
  })
})

describe('minLength', () => {
  it('compare la longueur, pas la valeur numérique', () => {
    expect(minLength('abc', 4)).toBeDefined()
    expect(minLength('abcd', 4)).toBeUndefined()
  })
})

describe('dateFinApresDebut / heureFinApresDebut', () => {
  it('dates : refuse une fin strictement avant le début, accepte l’égalité', () => {
    expect(dateFinApresDebut('2030-09-01', '2030-08-01')).toBeDefined()
    expect(dateFinApresDebut('2030-09-01', '2030-09-01')).toBeUndefined()
    expect(dateFinApresDebut('2030-09-01', '2030-10-01')).toBeUndefined()
  })

  it('heures : refuse aussi l’égalité (une séance ne peut pas durer 0 minute)', () => {
    expect(heureFinApresDebut('08:00', '08:00')).toBeDefined()
    expect(heureFinApresDebut('08:00', '07:59')).toBeDefined()
    expect(heureFinApresDebut('08:00', '09:00')).toBeUndefined()
  })

  it('ne valide rien tant que l’une des deux valeurs est absente', () => {
    expect(dateFinApresDebut('', '2030-09-01')).toBeUndefined()
    expect(heureFinApresDebut('08:00', '')).toBeUndefined()
  })
})

describe('validateFields / hasErrors', () => {
  it('ne conserve que les règles qui ont produit un message', () => {
    const errors = validateFields({
      nom: required(''),
      email: email('valide@aureole.ml'),
      age: positiveNumber(-1, 'Âge'),
    })
    expect(Object.keys(errors)).toEqual(['nom', 'age'])
    expect(hasErrors(errors)).toBe(true)
  })

  it('hasErrors est faux pour un objet vide', () => {
    expect(hasErrors({})).toBe(false)
  })
})
