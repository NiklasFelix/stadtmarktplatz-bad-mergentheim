import { Navigate } from 'react-router-dom'
import type { UserRole } from '../../types'
import { useAuthStore } from '../../store/useAuthStore'

interface ProtectedRouteProps {
  role: UserRole | UserRole[]
  children: React.ReactNode
}

export function ProtectedRoute({ role, children }: ProtectedRouteProps) {
  const user = useAuthStore((s) => s.currentUser)
  const roles = Array.isArray(role) ? role : [role]

  if (!user) {
    return <Navigate to="/" replace />
  }

  if (!roles.includes(user.role)) {
    return <Navigate to="/" replace />
  }

  return <>{children}</>
}
