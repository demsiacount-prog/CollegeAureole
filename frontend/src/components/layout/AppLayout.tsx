import { useState } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { Topbar } from './Topbar'
import { ErrorBoundary } from '@/components/ErrorBoundary'

/** Design system §28 — Shell applicatif.
 *  Layout fixe : sidebar + topbar + zone de contenu (seule cette dernière scrolle). */
export function AppLayout() {
  const [collapsed, setCollapsed] = useState(() => localStorage.getItem('aureole-sidebar-collapsed') === '1')
  const location = useLocation()

  const toggleSidebar = () =>
    setCollapsed((c) => {
      localStorage.setItem('aureole-sidebar-collapsed', c ? '0' : '1')
      return !c
    })

  return (
    <div className="app-shell">
      <Sidebar collapsed={collapsed} onToggle={toggleSidebar} />
      <div className="app-main">
        <Topbar />
        <main className="app-content">
          <div className="px-5 py-[18px]">
            <ErrorBoundary key={location.pathname}>
              <div key={location.pathname} className="animate-page-in">
                <Outlet />
              </div>
            </ErrorBoundary>
          </div>
        </main>
      </div>
    </div>
  )
}