import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from './AuthContext'
import type { Role } from '@/types'
import { Spinner } from '@/components/ui/Spinner'

export function ProtectedRoute() {
  const { isAuthenticated, isInitializing } = useAuth()
  const location = useLocation()

  if (isInitializing) {
    return (
      <div className="flex h-screen w-full items-center justify-center bg-[var(--color-base)]">
        <Spinner label="Vérification de la session…" />
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/connexion" state={{ from: location }} replace />
  }

  return <Outlet />
}

/** À placer sous <ProtectedRoute>, restreint l'accès à certains rôles. */
export function RoleRoute({ allow }: { allow: Role[] }) {
  const { user } = useAuth()

  if (!user) return null

  if (!allow.includes(user.role)) {
    return <Navigate to="/app/acces-refuse" replace />
  }

  return <Outlet />
}
