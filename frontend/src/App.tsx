import { lazy, Suspense, useEffect, useState } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from '@/auth/AuthContext'
import { ToastContainer } from '@/components/ui/ToastContainer'
import { ProtectedRoute, RoleRoute } from '@/auth/ProtectedRoute'
import { AppLayout } from '@/components/layout/AppLayout'
import { ErrorBoundary } from '@/components/ErrorBoundary'
import { Spinner } from '@/components/ui/Spinner'
import { LoginPage } from '@/pages/LoginPage'
import SetupWizard from '@/pages/SetupWizard'
import { AccessDeniedPage, NotFoundPage } from '@/pages/StatusPages'
import { Button } from '@/components/ui/Button'
import { ServerOff } from 'lucide-react'
import { NAV_SECTIONS } from '@/routes/nav'
import { useBackendUrl } from '@/hooks/useBackendUrl'
import { setApiBaseUrl, api } from '@/lib/api'

const loadDashboard = () => import('@/pages/DashboardPage')
const loadEleveList = () => import('@/features/eleves/EleveListPage')
const loadEleveDetail = () => import('@/features/eleves/EleveDetailPage')
const loadEnseignantList = () => import('@/features/enseignants/EnseignantListPage')
const loadEnseignantDetail = () => import('@/features/enseignants/EnseignantDetailPage')
const loadTuteurList = () => import('@/features/tuteurs/TuteurListPage')
const loadTuteurDetail = () => import('@/features/tuteurs/TuteurDetailPage')
const loadClasseList = () => import('@/features/classes/ClasseListPage')
const loadCoursList = () => import('@/features/cours/CoursListPage')
const loadNoteList = () => import('@/features/notes/NoteListPage')
const loadAbsenceList = () => import('@/features/absences/AbsenceListPage')
const loadInscriptionList = () => import('@/features/inscriptions/InscriptionListPage')
const loadSeanceList = () => import('@/features/seances/SeanceListPage')
const loadBulletinList = () => import('@/features/bulletins/BulletinListPage')
const loadBulletinDetail = () => import('@/features/bulletins/BulletinDetailPage')
const loadPaiementList = () => import('@/features/paiements/PaiementListPage')
const loadDepenseList = () => import('@/features/depenses/DepenseListPage')
const loadParametres = () => import('@/features/parametres/ParametresPage')
const loadResultatList = () => import('@/features/resultats/ResultatListPage')
const loadSalleList = () => import('@/features/salles/SalleListPage')
const loadCloture = () => import('@/features/cloture/CloturePage')
const loadPlaceholder = () => import('@/pages/PlaceholderPage')

const DashboardPage = lazy(loadDashboard)
const EleveListPage = lazy(loadEleveList)
const EleveDetailPage = lazy(loadEleveDetail)
const EnseignantListPage = lazy(loadEnseignantList)
const EnseignantDetailPage = lazy(loadEnseignantDetail)
const TuteurListPage = lazy(loadTuteurList)
const TuteurDetailPage = lazy(loadTuteurDetail)
const ClasseListPage = lazy(loadClasseList)
const CoursListPage = lazy(loadCoursList)
const NoteListPage = lazy(loadNoteList)
const AbsenceListPage = lazy(loadAbsenceList)
const InscriptionListPage = lazy(loadInscriptionList)
const SeanceListPage = lazy(loadSeanceList)
const BulletinListPage = lazy(loadBulletinList)
const BulletinDetailPage = lazy(loadBulletinDetail)
const PaiementListPage = lazy(loadPaiementList)
const DepenseListPage = lazy(loadDepenseList)
const ParametresPage = lazy(loadParametres)
const ResultatListPage = lazy(loadResultatList)
const SalleListPage = lazy(loadSalleList)
const CloturePage = lazy(loadCloture)
const PlaceholderPage = lazy(loadPlaceholder)

// Toutes les routes sont découpées (lazy) pour maîtriser le démarrage, mais on
// précharge les chunks en arrière-plan juste après le montage : la navigation
// ultérieure devient instantanée (le module est déjà en cache, plus d'attente
// de chargement/parse à chaque changement de page).
const ROUTE_PREFETCH: (() => Promise<unknown>)[] = [
  loadDashboard, loadEleveList, loadEleveDetail, loadEnseignantList,
  loadEnseignantDetail, loadTuteurList, loadTuteurDetail, loadClasseList,
  loadCoursList, loadNoteList, loadAbsenceList, loadInscriptionList,
  loadSeanceList, loadBulletinList, loadBulletinDetail, loadPaiementList,
  loadDepenseList, loadParametres, loadResultatList, loadSalleList,
  loadCloture, loadPlaceholder,
]

function prefetchRoutes() {
  for (const loader of ROUTE_PREFETCH) loader().catch(() => {})
}

const ALL_ROLES: import('@/types').Role[] = ['admin', 'directeur', 'comptable']
const DIRECTION: import('@/types').Role[] = ['admin', 'directeur']
const FINANCE: import('@/types').Role[] = ['admin', 'comptable']

const BUILT_MODULES = new Set([
  '/app/eleves', '/app/enseignants', '/app/tuteurs', '/app/classes', '/app/salles',
  '/app/cours', '/app/notes', '/app/absences', '/app/inscriptions',
  '/app/seances', '/app/bulletins', '/app/resultats', '/app/paiements',
  '/app/depenses', '/app/parametres', '/app/cloture-annee',
])

const moduleRoutes = NAV_SECTIONS.flatMap((section) => section.items).filter(
  (item) => item.path !== '/app' && !BUILT_MODULES.has(item.path),
)

function SuspenseRoute({ children }: { children: React.ReactNode }) {
  return <Suspense fallback={<div className="flex justify-center py-24"><Spinner /></div>}>{children}</Suspense>
}

function LoadingScreen() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-[var(--color-base)]">
      <div className="text-center">
        <Spinner />
        <p className="text-[var(--color-ink-dim)]">Démarrage du serveur...</p>
      </div>
    </div>
  )
}

function BackendErrorScreen({ backendUrl, onRetry }: { backendUrl: string; onRetry: () => void }) {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-[var(--color-base)] px-6 text-center">
      <ServerOff className="size-10 text-[var(--color-danger)]" strokeWidth={1.75} />
      <div>
        <h2 className="text-xl font-semibold text-[var(--color-ink)]">Serveur inaccessible</h2>
        <p className="mx-auto mt-1.5 max-w-md text-sm text-[var(--color-ink-dim)]">
          Impossible de joindre le service <span className="font-mono">{backendUrl}</span>. Vérifiez
          que le serveur est bien lancé puis réessayez.
        </p>
      </div>
      <Button variant="primary" onClick={onRetry}>
        Réessayer
      </Button>
    </div>
  )
}

export default function App() {
  const { backendUrl, ready } = useBackendUrl()
  const [setupState, setSetupState] = useState<'loading' | 'setup' | 'done' | 'error'>('loading')
  const [retryKey, setRetryKey] = useState(0)

  useEffect(() => {
    if (!ready || !backendUrl) return
    setApiBaseUrl(backendUrl)
    // Précharge les chunks de routes en arrière-plan pendant l'écran de
    // démarrage : la navigation sera instantanée dès le premier clic.
    prefetchRoutes()
    let attempts = 0
    let cancelled = false
    const tryCheck = () => {
      api.get<{ configured: boolean }>('/api/setup/status')
        .then((res) => {
          if (!cancelled) setSetupState(res.data.configured ? 'done' : 'setup')
        })
      .catch(() => {
        attempts += 1
        if (!cancelled && attempts < 20) setTimeout(tryCheck, 500)
        else if (!cancelled) setSetupState('error')
      })
    }
    tryCheck()
    return () => { cancelled = true }
  }, [ready, backendUrl, retryKey])

  if (!ready || setupState === 'loading') return <LoadingScreen />
  if (setupState === 'setup') return <SetupWizard />
  if (setupState === 'error') {
    return (
      <BackendErrorScreen
        backendUrl={backendUrl}
        onRetry={() => setRetryKey((k) => k + 1)}
      />
    )
  }

  return (
    <ErrorBoundary>
      <BrowserRouter>
        <AuthProvider>
          <ToastContainer />
          <Routes>
            <Route path="/connexion" element={<LoginPage />} />

            <Route element={<ProtectedRoute />}>
              <Route path="/app" element={<AppLayout />}>
                <Route index element={<SuspenseRoute><DashboardPage /></SuspenseRoute>} />
                <Route path="acces-refuse" element={<AccessDeniedPage />} />

                <Route element={<RoleRoute allow={ALL_ROLES} />}>
                  <Route path="eleves" element={<SuspenseRoute><EleveListPage /></SuspenseRoute>} />
                  <Route path="eleves/:matricule" element={<SuspenseRoute><EleveDetailPage /></SuspenseRoute>} />
                  <Route path="enseignants" element={<SuspenseRoute><EnseignantListPage /></SuspenseRoute>} />
                  <Route path="enseignants/:matricule" element={<SuspenseRoute><EnseignantDetailPage /></SuspenseRoute>} />
                  <Route path="tuteurs" element={<SuspenseRoute><TuteurListPage /></SuspenseRoute>} />
                  <Route path="tuteurs/:id" element={<SuspenseRoute><TuteurDetailPage /></SuspenseRoute>} />
                  <Route path="classes" element={<SuspenseRoute><ClasseListPage /></SuspenseRoute>} />
                  <Route path="salles" element={<SuspenseRoute><SalleListPage /></SuspenseRoute>} />
                </Route>

                <Route element={<RoleRoute allow={DIRECTION} />}>
                  <Route path="cours" element={<SuspenseRoute><CoursListPage /></SuspenseRoute>} />
                  <Route path="notes" element={<SuspenseRoute><NoteListPage /></SuspenseRoute>} />
                  <Route path="absences" element={<SuspenseRoute><AbsenceListPage /></SuspenseRoute>} />
                  <Route path="inscriptions" element={<SuspenseRoute><InscriptionListPage /></SuspenseRoute>} />
                  <Route path="seances" element={<SuspenseRoute><SeanceListPage /></SuspenseRoute>} />
                  <Route path="bulletins" element={<SuspenseRoute><BulletinListPage /></SuspenseRoute>} />
                  <Route path="bulletins/:id" element={<SuspenseRoute><BulletinDetailPage /></SuspenseRoute>} />
                  <Route path="resultats" element={<SuspenseRoute><ResultatListPage /></SuspenseRoute>} />
                </Route>

                <Route element={<RoleRoute allow={FINANCE} />}>
                  <Route path="paiements" element={<SuspenseRoute><PaiementListPage /></SuspenseRoute>} />
                  <Route path="depenses" element={<SuspenseRoute><DepenseListPage /></SuspenseRoute>} />
                </Route>

                <Route element={<RoleRoute allow={['admin', 'directeur']} />}>
                  <Route path="parametres" element={<SuspenseRoute><ParametresPage /></SuspenseRoute>} />
                </Route>

                <Route element={<RoleRoute allow={DIRECTION} />}>
                  <Route path="cloture-annee" element={<SuspenseRoute><CloturePage /></SuspenseRoute>} />
                </Route>

                {moduleRoutes.map((item) => (
                  <Route key={item.path} element={<RoleRoute allow={item.roles} />}>
                    <Route
                      path={item.path.replace('/app/', '')}
                      element={
                        <SuspenseRoute>
                          <PlaceholderPage title={item.label} icon={item.icon} />
                        </SuspenseRoute>
                      }
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
    </ErrorBoundary>
  )
}
