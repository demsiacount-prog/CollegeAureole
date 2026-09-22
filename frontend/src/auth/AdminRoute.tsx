import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from './useAuth'
import { isAdmin } from '@/routes/nav'
import { AccessDeniedPage } from '@/pages/StatusPages'
import { trace } from '@/lib/trace'

/** Route réservée aux administrateurs (RBAC) : les autres rôles voient une
 *  page « Accès refusé » ; un utilisateur non authentifié est renvoyé. */
export function AdminRoute() {
  const { isAuthenticated, isInitializing, user } = useAuth()

  if (isInitializing) {
    return <Navigate to="/connexion" replace />
  }

  if (!isAuthenticated) {
    trace('AdminRoute → redirection /connexion (non authentifié)')
    return <Navigate to="/connexion" replace />
  }

  if (!isAdmin(user?.role)) {
    trace('AdminRoute → accès refusé (rôle =', user?.role ?? 'aucun', ')')
    return <AccessDeniedPage />
  }

  return <Outlet />
}