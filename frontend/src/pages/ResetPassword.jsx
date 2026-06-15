import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { motion } from 'framer-motion'
import { useTranslation } from 'react-i18next'
import { Lock, Eye, EyeOff, ArrowRight, ArrowLeft, Loader2, CheckCircle } from 'lucide-react'
import { authAPI } from '../services/api'
import logoNavbar from '../assets/simutarget-logo-navbar.png'

function ResetPassword() {
  const { t } = useTranslation()
  const { token } = useParams()
  const navigate = useNavigate()
  const { register, handleSubmit, watch } = useForm()
  const [showPassword, setShowPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)

  const password = watch('password', '')

  const onSubmit = async (data) => {
    setError('')

    if (data.password !== data.confirmPassword) {
      setError(t('auth.passwordMismatch'))
      return
    }

    setIsLoading(true)
    try {
      await authAPI.resetPassword(token, data.password)
      setSuccess(true)
      setTimeout(() => navigate('/login'), 2500)
    } catch (e) {
      // Backend 400 → geçersiz/süresi dolmuş token; başka durumda generic
      const detail = e.response?.data?.detail
      setError(detail || t('auth.invalidResetLink'))
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div style={{ minHeight: '100vh', backgroundColor: 'var(--color-bg-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '24px' }}>
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} style={{ width: '100%', maxWidth: '440px' }}>
        {/* Logo */}
        <Link to="/" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '48px', textDecoration: 'none' }}>
          <img src={logoNavbar} alt="SimuTarget.ai" style={{ height: '44px', width: 'auto' }} />
        </Link>

        {/* Card */}
        <div className="card auth-card" style={{ padding: '48px' }}>
          <h1 style={{ fontSize: '28px', fontWeight: '700', textAlign: 'center', marginBottom: '8px' }}>{t('auth.resetPasswordTitle')}</h1>
          <p style={{ color: 'var(--color-text-muted)', textAlign: 'center', marginBottom: '32px' }}>{t('auth.resetPasswordSubtitle')}</p>

          {success ? (
            <div style={{ textAlign: 'center' }}>
              <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '20px' }}>
                <CheckCircle style={{ width: '48px', height: '48px', color: 'var(--color-accent-cyan)' }} />
              </div>
              <p style={{ color: 'var(--color-text-muted)', fontSize: '15px', lineHeight: '1.6', marginBottom: '32px' }}>
                {t('auth.resetSuccess')}
              </p>
              <Link to="/login" className="btn btn-primary" style={{ width: '100%', padding: '16px', fontSize: '16px', textDecoration: 'none', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
                <ArrowLeft style={{ width: '20px', height: '20px' }} /> {t('auth.backToLogin')}
              </Link>
            </div>
          ) : (
            <>
              {error && (
                <div style={{ marginBottom: '24px', padding: '16px', borderRadius: '12px', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.2)', color: 'var(--color-danger)', fontSize: '14px' }}>
                  {error}
                </div>
              )}

              <form onSubmit={handleSubmit(onSubmit)}>
                {/* New Password */}
                <div style={{ marginBottom: '24px' }}>
                  <label style={{ display: 'block', fontSize: '14px', fontWeight: '500', marginBottom: '8px' }}>{t('auth.newPassword')}</label>
                  <div style={{ position: 'relative' }}>
                    <Lock style={{ position: 'absolute', left: '16px', top: '50%', transform: 'translateY(-50%)', width: '20px', height: '20px', color: 'var(--color-text-muted)' }} />
                    <input type={showPassword ? 'text' : 'password'} {...register('password', { required: true, minLength: 8 })} className="input" style={{ paddingLeft: '48px', paddingRight: '48px' }} placeholder="••••••••" />
                    <button type="button" onClick={() => setShowPassword(!showPassword)}
                      style={{ position: 'absolute', right: '16px', top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--color-text-muted)' }}>
                      {showPassword ? <EyeOff style={{ width: '20px', height: '20px' }} /> : <Eye style={{ width: '20px', height: '20px' }} />}
                    </button>
                  </div>
                  <p style={{ marginTop: '8px', fontSize: '13px', color: 'var(--color-text-muted)' }}>{t('auth.passwordReq8')}</p>
                </div>

                {/* Confirm Password */}
                <div style={{ marginBottom: '32px' }}>
                  <label style={{ display: 'block', fontSize: '14px', fontWeight: '500', marginBottom: '8px' }}>{t('auth.confirmPassword')}</label>
                  <div style={{ position: 'relative' }}>
                    <Lock style={{ position: 'absolute', left: '16px', top: '50%', transform: 'translateY(-50%)', width: '20px', height: '20px', color: 'var(--color-text-muted)' }} />
                    <input type={showPassword ? 'text' : 'password'} {...register('confirmPassword', { required: true })} className="input" style={{ paddingLeft: '48px' }} placeholder="••••••••" />
                  </div>
                </div>

                {/* Submit */}
                <button type="submit" disabled={isLoading} className="btn btn-primary" style={{ width: '100%', padding: '16px', fontSize: '16px' }}>
                  {isLoading ? (
                    <><Loader2 style={{ width: '20px', height: '20px', animation: 'spin 1s linear infinite' }} /> {t('auth.resetting')}</>
                  ) : (
                    <>{t('auth.resetPasswordBtn')} <ArrowRight style={{ width: '20px', height: '20px' }} /></>
                  )}
                </button>
              </form>

              <p style={{ marginTop: '32px', textAlign: 'center', color: 'var(--color-text-muted)', fontSize: '14px' }}>
                <Link to="/login" style={{ color: 'var(--color-accent-cyan)', textDecoration: 'none', fontWeight: '500' }}>{t('auth.backToLogin')}</Link>
              </p>
            </>
          )}
        </div>
      </motion.div>
    </div>
  )
}

export default ResetPassword
