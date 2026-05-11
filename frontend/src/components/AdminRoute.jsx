// frontend/src/components/AdminRoute.jsx
import { Navigate } from 'react-router-dom'
import { useEffect, useState } from 'react'
import useAuthStore from '../stores/authStore'

/**
 * Admin yetkisi gerektiren route'ları sarmalayan component.
 *
 * Akış:
 *   1. Auth değilse → /login
 *   2. user null ise (sayfa reload sonrası) → fetchProfile çağır, bekle
 *   3. user.role !== 'admin' → /dashboard (sessizce)
 *   4. user.role === 'admin' → children render et
 *
 * Backend'de ayrıca 403 kontrolü var, bu sadece UX katmanı.
 */
function AdminRoute({ children }) {
  const { isAuthenticated, user, fetchProfile } = useAuthStore()
  const [checking, setChecking] = useState(!user)

  useEffect(() => {
    let mounted = true

    const verifyAdmin = async () => {
      if (!isAuthenticated) {
        if (mounted) setChecking(false)
        return
      }
      if (!user) {
        await fetchProfile()
      }
      if (mounted) setChecking(false)
    }

    verifyAdmin()

    return () => {
      mounted = false
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (checking) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-gray-500 text-sm">Yetki doğrulanıyor…</div>
      </div>
    )
  }

  if (user?.role !== 'admin') {
    return <Navigate to="/dashboard" replace />
  }

  return children
}

export default AdminRoute
