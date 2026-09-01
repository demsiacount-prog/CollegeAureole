import { lazy, Suspense, useEffect, useState } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from '@/auth/AuthContext'
import { ToastContainer } from '@/components/ui/ToastContainer'
import { ServerGate } from '@/components/ServerGate'
import { ProtectedRoute, RoleRoute } from '@/auth/ProtectedRoute'
import { AppLayout } from '@/components/layout/AppLayout'
import { ErrorBoundary } from '@/components/ErrorBoundary'
import { Spinner } from '@/components/ui/Spinner'
import { LoginPage } from '@/pages/LoginPage'
import SetupWizard from '@/pages/SetupWizard'
import { AccessDeniedPage, NotFoundPage } from '@/pages/StatusPages'
import { api } from '@/lib/api'

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

const ALL_ROLES: import('@/types').Role[] = ['admin', 'directeur', 'comptable']
const DIRECTION: import('@/types').Role[] = ['admin', 'directeur']
const FINANCE: import('@/types').Role[] = ['admin', 'comptable']

function SuspenseRoute({ children }: { children: React.ReactNode }) {
  return <Suspense fallback={<div className="flex justify-center py-24"><Spinner /></div>}>{children}</Suspense>
}

/** Vérifie si l'établissement a déjà été configuré, et affiche l'assistant de
 *  configuration initiale sinon. Ce composant doit être monté SOUS ServerGate :
 *  en mode bureau, tant que le serveur local n'est pas validé, resoudreBaseUrl()
 *  renvoie une base vide et l'appel /api/setup/status échoue silencieusement
 *  (tombant dans le .catch), ce qui masquait l'assistant de configuration lors
 *  du tout premier lancement du client bureau. */
function SetupGate({ children }: { children: React.ReactNode }) {
  const [setupState, setSetupState] = useState<'loading' | 'setup' | 'done'>('loading')

  useEffect(() => {
    api.get<{ configured: boolean }>('/api/setup/status')
      .then((res) => setSetupState(res.data.configured ? 'done' : 'setup'))
      .catch(() => setSetupState('done'))
  }, [])

  if (setupState === 'loading') {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Spinner />
      </div>
    )
  }
  if (setupState === 'setup') return <SetupWizard />
  return <>{children}</>
}

export default function App() {
  return (
    <ErrorBoundary>
      <ServerGate>
        <SetupGate>
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
              </Route>
            </Route>

            <Route path="/" element={<Navigate to="/app" replace />} />
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
        </SetupGate>
      </ServerGate>
    </ErrorBoundary>
  )
}
