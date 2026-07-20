import { api } from '@/lib/api'
import type { Tuteur } from '@/features/shared/types'

export async function fetchTuteurs(): Promise<Tuteur[]> {
  const res = await api.get<Tuteur[]>('/api/tuteurs/', { params: { limit: 500 } })
  return res.data
}
