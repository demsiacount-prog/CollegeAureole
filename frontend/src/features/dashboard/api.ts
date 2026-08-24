import { api } from '@/lib/api'
import type { DashboardStatsResponse, DashboardFinanceResponse } from './types'

export async function fetchDashboardStats(): Promise<DashboardStatsResponse> {
  const res = await api.get<DashboardStatsResponse>('/api/dashboard/stats')
  return res.data
}

export async function fetchDashboardFinances(): Promise<DashboardFinanceResponse> {
  const res = await api.get<DashboardFinanceResponse>('/api/dashboard/finances')
  return res.data
}
