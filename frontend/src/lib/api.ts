import axios from 'axios'

export const TOKEN_STORAGE_KEY = 'aureole_token'

// En mode serveur (frontend servi par le backend), l'API est sur la même
// origine : window.location.origin. VITE_API_URL reste un sur-ensemble pour le
// développement (vite dev pointe alors vers http://localhost:3000).
const FALLBACK_URL =
  import.meta.env.VITE_API_URL ||
  (typeof window !== 'undefined' ? window.location.origin : 'http://localhost:3000')

export const api = axios.create({
  baseURL: FALLBACK_URL,
  timeout: 30_000,
})

export function setApiBaseUrl(url: string) {
  api.defaults.baseURL = url
}

api.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_STORAGE_KEY)
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export const AUTH_EXPIRED_EVENT = 'aureole:auth-expired'

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      window.dispatchEvent(new CustomEvent(AUTH_EXPIRED_EVENT))
    }
    return Promise.reject(error)
  },
)

export function extractErrorMessage(error: unknown, fallback = 'Une erreur est survenue.'): string {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data as
      | { message?: string; detail?: unknown }
      | undefined
    if (data) {
      if (typeof data.message === 'string') return data.message
      if (typeof data.detail === 'string') return data.detail
      if (
        data.detail &&
        typeof data.detail === 'object' &&
        typeof (data.detail as { message?: unknown }).message === 'string'
      ) {
        return (data.detail as { message: string }).message
      }
    }
  }
  return fallback
}
