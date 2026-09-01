import { useQuery } from '@tanstack/react-query'
import { useAuth } from '@/auth/useAuth'
import { fetchAbsencesTotal } from '@/features/absences/api'
import type { Role } from '@/types'

/** Accès par chemin aux items de nav qui comportent un badge compte (design system §06.2). */
const BADGED_PATHS: { path: string; roles: Role[] }[] = [
  { path: '/app/absences', roles: ['admin', 'directeur'] },
]

export function useNavBadges(): Record<string, number> {
  const { user } = useAuth()
  const enabledPaths = BADGED_PATHS.filter((p) => user && p.roles.includes(user.role))

  const absences = useQuery({
    queryKey: ['nav-badge', 'absences-non-justifiees'],
    queryFn: () => fetchAbsencesTotal({ justifiee: false }),
    enabled: enabledPaths.some((p) => p.path === '/app/absences'),
    staleTime: 60_000,
  })

  const badges: Record<string, number> = {}
  if (enabledPaths.some((p) => p.path === '/app/absences') && (absences.data ?? 0) > 0) {
    badges['/app/absences'] = absences.data ?? 0
  }
  return badges
}
