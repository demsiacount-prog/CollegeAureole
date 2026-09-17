import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from './useAuth'
import { Spinner } from '@/components/ui/Spinner'
import { trace } from '@/lib/trace'

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
    trace('ProtectedRoute → redirection /connexion (non authentifié)')
    return <Navigate to="/connexion" state={{ from: location }} replace />
  }

  return <Outlet />
}