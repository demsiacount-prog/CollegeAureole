import { act, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { AuthProvider } from './AuthContext'
import { useAuth } from './useAuth'
import { AUTH_EXPIRED_EVENT, TOKEN_STORAGE_KEY } from '@/lib/api'

const { apiGet, apiPost } = vi.hoisted(() => ({ apiGet: vi.fn(), apiPost: vi.fn() }))

vi.mock('@/lib/api', async (importOriginal) => {
  const reel = await importOriginal<typeof import('@/lib/api')>()
  return { ...reel, api: { get: apiGet, post: apiPost } }
})

const UTILISATEUR = { id: 1, nom: 'Diarra', prenom: 'Fatoumata', email: 'admin@aureole.ml', role: 'ADMIN' }

/** Sonde qui affiche l'état du contexte pour l'observer depuis les tests. */
function Sonde() {
  const { user, isAuthenticated, isInitializing } = useAuth()
  return (
    <div>
      <span data-testid="initializing">{String(isInitializing)}</span>
      <span data-testid="authenticated">{String(isAuthenticated)}</span>
      <span data-testid="email">{user?.email ?? ''}</span>
    </div>
  )
}

function rendreAvecAction() {
  let actions: ReturnType<typeof useAuth> | null = null
  function Capture() {
    actions = useAuth()
    return <Sonde />
  }
  render(
    <AuthProvider>
      <Capture />
    </AuthProvider>,
  )
  return () => actions!
}

describe('AuthProvider', () => {
  beforeEach(() => {
    localStorage.clear()
    apiGet.mockReset()
    apiPost.mockReset()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('sans token en mémoire : termine l’initialisation aussitôt, non authentifié', async () => {
    rendreAvecAction()

    await waitFor(() => expect(screen.getByTestId('initializing')).toHaveTextContent('false'))
    expect(screen.getByTestId('authenticated')).toHaveTextContent('false')
    expect(apiGet).not.toHaveBeenCalled()
  })

  it('avec un token valide en mémoire : recharge l’utilisateur via /api/auth/moi', async () => {
    localStorage.setItem(TOKEN_STORAGE_KEY, 'jeton-valide')
    apiGet.mockResolvedValueOnce({ data: UTILISATEUR })

    rendreAvecAction()

    await waitFor(() => expect(screen.getByTestId('authenticated')).toHaveTextContent('true'))
    expect(screen.getByTestId('email')).toHaveTextContent('admin@aureole.ml')
    expect(apiGet).toHaveBeenCalledWith('/api/auth/moi')
  })

  it('token invalide : /api/auth/moi échoue -> token retiré, session non authentifiée', async () => {
    localStorage.setItem(TOKEN_STORAGE_KEY, 'jeton-perime')
    apiGet.mockRejectedValueOnce({ isAxiosError: true, response: { status: 401 } })

    rendreAvecAction()

    await waitFor(() => expect(screen.getByTestId('initializing')).toHaveTextContent('false'))
    expect(screen.getByTestId('authenticated')).toHaveTextContent('false')
    expect(localStorage.getItem(TOKEN_STORAGE_KEY)).toBeNull()
  })

  it('condition de course : un token remplacé pendant la vérification n’est pas effacé par l’échec de l’ancien', async () => {
    localStorage.setItem(TOKEN_STORAGE_KEY, 'ancien-jeton')
    let rejeter!: (raison: unknown) => void
    apiGet.mockReturnValueOnce(new Promise((_res, rej) => { rejeter = rej }))

    rendreAvecAction()

    // Une reconnexion remplace le token pendant que l'appel /api/auth/moi
    // pour l'ANCIEN token est encore en vol.
    localStorage.setItem(TOKEN_STORAGE_KEY, 'nouveau-jeton')
    act(() => rejeter({ isAxiosError: true, response: { status: 401 } }))

    await waitFor(() => expect(screen.getByTestId('initializing')).toHaveTextContent('false'))
    expect(localStorage.getItem(TOKEN_STORAGE_KEY)).toBe('nouveau-jeton')
  })

  it('login réussi : stocke le token et authentifie l’utilisateur', async () => {
    apiPost.mockResolvedValueOnce({ data: { access_token: 'nouveau-jeton', utilisateur: UTILISATEUR } })
    const getActions = rendreAvecAction()
    await waitFor(() => expect(screen.getByTestId('initializing')).toHaveTextContent('false'))

    await act(async () => {
      await getActions().login('admin@aureole.ml', 'motdepasse123')
    })

    expect(localStorage.getItem(TOKEN_STORAGE_KEY)).toBe('nouveau-jeton')
    expect(screen.getByTestId('authenticated')).toHaveTextContent('true')
  })

  it('login échoué : ne stocke aucun token et propage un message lisible', async () => {
    apiPost.mockRejectedValueOnce({
      isAxiosError: true,
      response: { status: 401, data: { message: 'Identifiants invalides.' } },
    })
    const getActions = rendreAvecAction()
    await waitFor(() => expect(screen.getByTestId('initializing')).toHaveTextContent('false'))

    await expect(
      act(async () => {
        await getActions().login('admin@aureole.ml', 'mauvais-mdp')
      }),
    ).rejects.toThrow('Identifiants invalides.')

    expect(localStorage.getItem(TOKEN_STORAGE_KEY)).toBeNull()
    expect(screen.getByTestId('authenticated')).toHaveTextContent('false')
  })

  it('logout() efface le token et l’utilisateur courant', async () => {
    localStorage.setItem(TOKEN_STORAGE_KEY, 'jeton-valide')
    apiGet.mockResolvedValueOnce({ data: UTILISATEUR })
    const getActions = rendreAvecAction()
    await waitFor(() => expect(screen.getByTestId('authenticated')).toHaveTextContent('true'))

    act(() => getActions().logout())

    expect(screen.getByTestId('authenticated')).toHaveTextContent('false')
    expect(localStorage.getItem(TOKEN_STORAGE_KEY)).toBeNull()
  })

  it('l’événement global de session expirée déclenche une déconnexion', async () => {
    localStorage.setItem(TOKEN_STORAGE_KEY, 'jeton-valide')
    apiGet.mockResolvedValueOnce({ data: UTILISATEUR })
    rendreAvecAction()
    await waitFor(() => expect(screen.getByTestId('authenticated')).toHaveTextContent('true'))

    act(() => window.dispatchEvent(new CustomEvent(AUTH_EXPIRED_EVENT)))

    expect(screen.getByTestId('authenticated')).toHaveTextContent('false')
    expect(localStorage.getItem(TOKEN_STORAGE_KEY)).toBeNull()
  })
})
