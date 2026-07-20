import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from '@/auth/AuthContext'
import { ProtectedRoute, RoleRoute } from '@/auth/ProtectedRoute'
import { AppLayout } from '@/components/layout/AppLayout'
import { LoginPage } from '@/pages/LoginPage'
import { DashboardPage } from '@/pages/DashboardPage'
import { PlaceholderPage } from '@/pages/PlaceholderPage'
import { AccessDeniedPage, NotFoundPage } from '@/pages/StatusPages'
import { EleveListPage } from '@/features/eleves/EleveListPage'
import { EleveDetailPage } from '@/features/eleves/EleveDetailPage'
import { NAV_SECTIONS } from '@/routes/nav'

// Modules déjà construits avec leurs propres pages ; le reste retombe sur
// une page "en construction" générée depuis la config du menu.
const BUILT_MODULES = new Set(['/app/eleves'])

const moduleRoutes = NAV_SECTIONS.flatMap((section) => section.items).filter(
  (item) => item.path !== '/app' && !BUILT_MODULES.has(item.path),
)

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/connexion" element={<LoginPage />} />

          <Route element={<ProtectedRoute />}>
            <Route path="/app" element={<AppLayout />}>
              <Route index element={<DashboardPage />} />
              <Route path="acces-refuse" element={<AccessDeniedPage />} />

              <Route path="eleves" element={<EleveListPage />} />
              <Route path="eleves/:matricule" element={<EleveDetailPage />} />

              {moduleRoutes.map((item) => (
                <Route key={item.path} element={<RoleRoute allow={item.roles} />}>
                  <Route
                    path={item.path.replace('/app/', '')}
                    element={<PlaceholderPage title={item.label} icon={item.icon} />}
                  />
                </Route>
              ))}
            </Route>
          </Route>

          <Route path="/" element={<Navigate to="/app" replace />} />
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}
