import { api } from '@/lib/api'
import type { Classe } from '@/features/shared/types'

export async function fetchClasses(): Promise<Classe[]> {
  const res = await api.get<Classe[]>('/api/classes/', { params: { limit: 500 } })
  return res.data
}
