import { api } from '@/lib/api'
import type { DashboardStatsResponse } from './types'

export async function fetchDashboardStats(): Promise<DashboardStatsResponse> {
  const res = await api.get<DashboardStatsResponse>('/api/dashboard/stats')
  return res.data
}
