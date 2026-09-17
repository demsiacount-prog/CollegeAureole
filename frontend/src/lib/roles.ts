const LIBELLES: Record<string, string> = {
  ADMIN: 'Administrateur',
  DIRECTEUR: 'Directeur',
  COMPTABLE: 'Comptable',
  SECRETAIRE: 'Secrétaire',
}

/** Libellé lisible d'un rôle utilisateur, avec repli sur l'original en majuscule. */
export function roleLabel(role?: string | null): string {
  if (!role) return 'Utilisateur'
  return LIBELLES[role.toUpperCase()] ?? role
}