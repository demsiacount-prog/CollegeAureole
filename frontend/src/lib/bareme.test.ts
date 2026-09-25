import { describe, expect, it } from 'vitest'
import { appreciation, baremeNiveau, estEf1, estSixieme, noteColor, utiliseCoefficient } from './bareme'

// Cette règle est le cœur du calcul des moyennes (miroir de
// `_bareme_niveau` côté backend, `services/bareme.py`) : 1ère-6ème Année
// (1er cycle, EF1) notées /10 ; 7-9ème Année, lycée et jardin notés /20.
describe('baremeNiveau', () => {
  it.each([
    ['1ère Année', 10],
    ['2ème Année', 10],
    ['5ème Année', 10],
    ['6ème Année', 10],
    ['7ème Année', 20],
    ['9ème Année', 20],
  ])('%s -> /%d', (niveau, attendu) => {
    expect(baremeNiveau(niveau)).toBe(attendu)
  })

  it.each(['Terminale', 'Tle', 'Première', 'Premiere', 'Seconde', '2nde', '2de', '1ère'])(
    'niveau lycée "%s" -> /20',
    (niveau) => {
      expect(baremeNiveau(niveau)).toBe(20)
    },
  )

  it.each(['Petite Section', 'Moyenne Section', 'Grande Section'])(
    'niveau jardin "%s" -> /20 (pas de parsing numérique)',
    (niveau) => {
      expect(baremeNiveau(niveau)).toBe(20)
    },
  )

  it('est insensible à la casse et aux espaces', () => {
    expect(baremeNiveau('  3ÈME ANNÉE  ')).toBe(10)
  })

  it('valeur vide ou inconnue retombe sur /20 (jamais /10 par erreur)', () => {
    expect(baremeNiveau('')).toBe(20)
    expect(baremeNiveau('Niveau inconnu')).toBe(20)
  })

  it('accepte null/undefined sans lever d’exception', () => {
    // @ts-expect-error – on vérifie la robustesse face à un niveau manquant,
    // comme peut le renvoyer une réponse API incomplète.
    expect(() => baremeNiveau(null)).not.toThrow()
    // @ts-expect-error idem
    expect(baremeNiveau(undefined)).toBe(20)
  })
})

describe('estSixieme / estEf1', () => {
  it('la 6ème Année reste au barème /10 (EF1) mais est signalée comme classe spéciale', () => {
    expect(estSixieme('6ème Année')).toBe(true)
    expect(estEf1('6ème Année')).toBe(true)
  })

  it('1ère à 5ème Année sont EF1, pas "6ème"', () => {
    for (const n of ['1ère Année', '2ème Année', '3ème Année', '4ème Année', '5ème Année']) {
      expect(estSixieme(n)).toBe(false)
      expect(estEf1(n)).toBe(true)
    }
  })
})

describe('utiliseCoefficient', () => {
  it('une COMPOSITION est toujours en moyenne simple, quel que soit le niveau', () => {
    expect(utiliseCoefficient('1ère Année', 'COMPOSITION')).toBe(false)
    expect(utiliseCoefficient('6ème Année', 'COMPOSITION')).toBe(false)
    expect(utiliseCoefficient('Terminale', 'COMPOSITION')).toBe(false)
  })

  it('un TRIMESTRE en EF2/lycée utilise les coefficients', () => {
    expect(utiliseCoefficient('7ème Année', 'TRIMESTRE')).toBe(true)
    expect(utiliseCoefficient('Terminale', 'TRIMESTRE')).toBe(true)
  })

  it('un TRIMESTRE en EF1 (hors 6ème) est en moyenne simple', () => {
    expect(utiliseCoefficient('3ème Année', 'TRIMESTRE')).toBe(false)
  })

  it('un TRIMESTRE de 6ème Année utilise les coefficients malgré le barème /20', () => {
    expect(utiliseCoefficient('6ème Année', 'TRIMESTRE')).toBe(true)
  })
})

describe('noteColor', () => {
  it.each([
    [18, 20, 'success'],
    [16, 20, 'success'],
    [13, 20, 'neutral'],
    [10.5, 20, 'warning'],
    [8, 20, 'danger'],
    [0, 20, 'danger'],
  ])('note %d/%d -> %s', (n, bareme, attendu) => {
    expect(noteColor(n, bareme)).toBe(attendu)
  })

  it('les seuils sont relatifs au barème, pas à une échelle /20 fixe', () => {
    // 8/10 = 80% -> même couleur que 16/20 = 80%.
    expect(noteColor(8, 10)).toBe(noteColor(16, 20))
  })
})

describe('appreciation', () => {
  it.each([
    [19, 20, 'Excellent'],
    [17, 20, 'Très bien'],
    [15, 20, 'Bien'],
    [13, 20, 'Assez bien'],
    [11, 20, 'Passable'],
    [5, 20, 'Insuffisant'],
  ])('%d/%d -> %s', (n, bareme, attendu) => {
    expect(appreciation(n, bareme)).toBe(attendu)
  })
})
