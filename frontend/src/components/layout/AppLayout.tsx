import { useState } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import { Lock } from 'lucide-react'
import { Sidebar } from './Sidebar'
import { Topbar } from './Topbar'
import { ErrorBoundary } from '@/components/ErrorBoundary'
import { useLectureSeule } from '@/features/annees_scolaires/useLectureSeule'

/** Design system §28 — Shell applicatif.
 *  Layout fixe : sidebar + topbar + zone de contenu (seule cette dernière scrolle). */
export function AppLayout() {
  const [collapsed, setCollapsed] = useState(() => localStorage.getItem('aureole-sidebar-collapsed') === '1')
  const location = useLocation()
  const { lectureSeule } = useLectureSeule()

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
        {lectureSeule && (
          <div className="flex shrink-0 items-center gap-2 border-b border-[var(--color-warning)]/30 bg-[var(--color-warning-wash)] px-4 py-1.5 text-[12.5px] text-[var(--color-warning)]">
            <Lock className="size-3.5 shrink-0" strokeWidth={2} />
            <span>
              Année scolaire clôturée — consultation en lecture seule. Les modifications sont désactivées.
            </span>
          </div>
        )}
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