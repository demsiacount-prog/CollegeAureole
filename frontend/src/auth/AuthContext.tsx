import { useCallback, useEffect, useState, type ReactNode } from 'react'
import { api, AUTH_EXPIRED_EVENT, extractErrorMessage, traceToken, TOKEN_STORAGE_KEY } from '@/lib/api'
import { trace } from '@/lib/trace'
import type { TokenResponse, Utilisateur } from '@/types'
import { AuthContext } from './auth-context'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<Utilisateur | null>(null)
  const [isInitializing, setIsInitializing] = useState(true)

  const logout = useCallback(() => {
    const avant = localStorage.getItem(TOKEN_STORAGE_KEY)
    localStorage.removeItem(TOKEN_STORAGE_KEY)
    setUser(null)
    trace('logout()', 'jwt effacé:', traceToken(avant))
  }, [])

  useEffect(() => {
    const token = localStorage.getItem(TOKEN_STORAGE_KEY)
    trace('démarrage AuthProvider, présent =', traceToken(token))
    if (!token) {
      setIsInitializing(false)
      return
    }
    api
      .get<Utilisateur>('/api/auth/moi')
      .then((res) => {
        trace('/api/auth/moi OK, utilisateur =', res.data.email)
        setUser(res.data)
      })
      .catch(() => {
        // Ne jamais effacer un token qui aurait été remplacé pendant la
        // vérification (reconnexion effectuée tandis que ce contrôle d'un
        // ancien token était en vol).
        if (localStorage.getItem(TOKEN_STORAGE_KEY) === token) {
          trace('/api/auth/moi en échec → token courant retiré')
          localStorage.removeItem(TOKEN_STORAGE_KEY)
        } else {
          trace('/api/auth/moi en échec mais token remplacé → on le conserve')
        }
      })
      .finally(() => setIsInitializing(false))
  }, [])

  useEffect(() => {
    const handleExpired = () => {
      trace('événement auth-expired reçu → déconnexion')
      logout()
    }
    window.addEventListener(AUTH_EXPIRED_EVENT, handleExpired)
    return () => window.removeEventListener(AUTH_EXPIRED_EVENT, handleExpired)
  }, [logout])

  const login = useCallback(async (email: string, motDePasse: string) => {
    trace('tentative de connexion', email)
    try {
      const res = await api.post<TokenResponse>('/api/auth/connexion', {
        email,
        mot_de_passe: motDePasse,
      })
      trace('connexion OK → stockage token', traceToken(res.data.access_token))
      localStorage.setItem(TOKEN_STORAGE_KEY, res.data.access_token)
      setUser(res.data.utilisateur)
    } catch (error) {
      throw new Error(extractErrorMessage(error, 'Connexion impossible.'))
    }
  }, [])

  return (
    <AuthContext.Provider
      value={{ user, isInitializing, isAuthenticated: !!user, login, logout }}
    >
      {children}
    </AuthContext.Provider>
  )
}

