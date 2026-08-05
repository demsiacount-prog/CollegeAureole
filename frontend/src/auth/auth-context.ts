import { createContext } from 'react'
import type { Utilisateur } from '@/types'

export interface AuthContextValue {
  user: Utilisateur | null
  /** true pendant la vérification initiale du token au chargement de l'app */
  isInitializing: boolean
  isAuthenticated: boolean
  login: (email: string, motDePasse: string) => Promise<void>
  logout: () => void
}

export const AuthContext = createContext<AuthContextValue | undefined>(undefined)
