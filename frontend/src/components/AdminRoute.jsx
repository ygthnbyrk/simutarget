// frontend/src/components/AdminRoute.jsx
import { Navigate } from 'react-router-dom'
import { useEffect, useState } from 'react'
import useAuthStore from '../stores/authStore'

/**
 * Admin yetkisi gerektiren route'ları sarmalayan component.
 *
 * Akış (sıralama önemli):
 *   1. Mount → checking=true, loader göster (henüz karar yok)
 *   2. useEffect: localStorage'da token var mı?
 *      - Yok → checking=false → /login
 *      - Var → user yüklü mü?
 *          - Hayır → fetchProfile() çağır → checking=false
 *          - Evet → checking=false
 *   3. Render:
 *      - checking ise loader
 *      - token yoksa /login
 *      - user yoksa (profile çekemedi) /login
 *      - user.role !== 'admin' ise /dashboard
 *      - aksi takdirde children
 *
 * Backend'de ayrıca 403 kontrolü var, bu sadece UX katmanı.
 */
function AdminRoute({ children }) {
  const { user, fetchProfile } = useAuthStore()
  const [checking, setChecking] = useState(true)

  useEffect(() => {
    let mounted = true

    const verifyAdmin = async () => {
      const localToken = localStorage.getItem('token')

      if (!localToken) {
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

  if (checking) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-gray-500 text-sm">Yetki doğrulanıyor…</div>
      </div>
    )
  }

  if (!localStorage.getItem('token')) {
    return <Navigate to="/login" replace />
  }

  if (!user) {
    return <Navigate to="/login" replace />
  }

  if (user.role !== 'admin') {
    return <Navigate to="/dashboard" replace />
  }

  return children
}

export default AdminRoute
