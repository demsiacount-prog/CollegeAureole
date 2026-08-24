import { useAuth } from '@/auth/useAuth'
import DashboardFinances from '@/features/dashboard/DashboardFinances'
import DashboardDirection from '@/features/dashboard/DashboardDirection'

export default function DashboardPage() {
  const { user } = useAuth()

  if (user?.role === 'comptable') {
    return <DashboardFinances />
  }
  return <DashboardDirection />
}
