import { Outlet, useLocation } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { Topbar } from './Topbar'
import { ErrorBoundary } from '@/components/ErrorBoundary'
import { DemoTour } from '@/features/demo/DemoTour'

export function AppLayout() {
  const location = useLocation()
  return (
    <div className="flex h-screen w-full bg-[var(--color-base)]">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar />
        <main className="flex-1 overflow-y-auto px-10 py-8">
          <div className="mx-auto max-w-[1400px]">
            <ErrorBoundary key={location.pathname}>
              <div key={location.pathname} className="animate-page-in">
                <Outlet />
              </div>
            </ErrorBoundary>
          </div>
        </main>
      </div>
      <DemoTour />
    </div>
  )
}
