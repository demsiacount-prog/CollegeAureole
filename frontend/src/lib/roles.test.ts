import { describe, expect, it } from 'vitest'
import { roleLabel } from './roles'

describe('roleLabel', () => {
  it.each([
    ['ADMIN', 'Administrateur'],
    ['DIRECTEUR', 'Directeur'],
    ['COMPTABLE', 'Comptable'],
    ['SECRETAIRE', 'Secrétaire'],
    ['ENSEIGNANT', 'Enseignant'],
  ])('%s -> %s', (role, attendu) => {
    expect(roleLabel(role)).toBe(attendu)
  })

  it('est insensible à la casse (rôle stocké en minuscules par erreur, par ex.)', () => {
    expect(roleLabel('admin')).toBe('Administrateur')
  })

  it('retombe sur "Utilisateur" si le rôle est absent', () => {
    expect(roleLabel(null)).toBe('Utilisateur')
    expect(roleLabel(undefined)).toBe('Utilisateur')
    expect(roleLabel('')).toBe('Utilisateur')
  })

  it('retourne le rôle brut (non traduit) si inconnu, plutôt que de le masquer', () => {
    expect(roleLabel('SURVEILLANT')).toBe('SURVEILLANT')
  })
})
