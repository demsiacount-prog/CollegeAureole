import { useCallback, useEffect, useState, type ReactNode } from 'react'
import { api, AUTH_EXPIRED_EVENT, extractErrorMessage, TOKEN_STORAGE_KEY } from '@/lib/api'
import type { TokenResponse, Utilisateur } from '@/types'
import { AuthContext } from './auth-context'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<Utilisateur | null>(null)
  const [isInitializing, setIsInitializing] = useState(true)

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_STORAGE_KEY)
    setUser(null)
  }, [])

  useEffect(() => {
    const token = localStorage.getItem(TOKEN_STORAGE_KEY)
    if (!token) {
      setIsInitializing(false)
      return
    }
    api
      .get<Utilisateur>('/api/auth/moi')
      .then((res) => setUser(res.data))
      .catch(() => {
        localStorage.removeItem(TOKEN_STORAGE_KEY)
      })
      .finally(() => setIsInitializing(false))
  }, [])

  useEffect(() => {
    const handleExpired = () => logout()
    window.addEventListener(AUTH_EXPIRED_EVENT, handleExpired)
    return () => window.removeEventListener(AUTH_EXPIRED_EVENT, handleExpired)
  }, [logout])

  const login = useCallback(async (email: string, motDePasse: string) => {
    try {
      const res = await api.post<TokenResponse>('/api/auth/connexion', {
        email,
        mot_de_passe: motDePasse,
      })
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

