import { useState, useRef } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { motion } from 'framer-motion'
import { GoogleLogin } from '@react-oauth/google'
import { useTranslation } from 'react-i18next'
import { Mail, Lock, User, Eye, EyeOff, ArrowRight, Loader2, Check } from 'lucide-react'
import useAuthStore from '../stores/authStore'
import TurnstileWidget from '../components/TurnstileWidget'
import logoNavbar from '../assets/simutarget-logo-navbar.png'

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID
const TURNSTILE_SITE_KEY = import.meta.env.VITE_TURNSTILE_SITE_KEY
const turnstileEnabled = !!TURNSTILE_SITE_KEY

// İsimde reddedilecek desenler (backend _validate_name ile simetrik — anlık geri bildirim)
const NAME_BANNED = /(https?:\/\/|www\.|\.com|\.net|\.org|\.ru|\.xyz|\.io|bit\.ly|t\.me|telegram|@|<|>)/i

function Register() {
  const [showPassword, setShowPassword] = useState(false)
  const [turnstileToken, setTurnstileToken] = useState('')
  const turnstileRef = useRef(null)
  const navigate = useNavigate()
  const { t } = useTranslation()
  const { register: registerUser, loginWithGoogle, isLoading, error, clearError } = useAuthStore()
  const { register, handleSubmit, formState: { errors }, watch } = useForm()
  const password = watch('password', '')

  const passwordRequirements = [
    { met: password.length >= 8, text: t('auth.passwordReq8') },
    { met: /[A-Z]/.test(password), text: t('auth.passwordReqUpper') },
    { met: /[0-9]/.test(password), text: t('auth.passwordReqNumber') },
  ]

  const onSubmit = async (data) => {
    clearError()
    if (turnstileEnabled && !turnstileToken) return
    const result = await registerUser(data.email, data.password, data.name, turnstileToken, data.website)
    // Token tek kullanımlık — sonuç ne olursa olsun taze token için reset et
    turnstileRef.current?.reset()
    setTurnstileToken('')
    if (result.success) navigate('/dashboard')
  }

  const handleGoogleSuccess = async (credentialResponse) => {
    clearError()
    const result = await loginWithGoogle(credentialResponse.credential)
    if (result.success) navigate('/dashboard')
  }

  const handleGoogleError = () => {
    console.error('Google login failed')
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
          <h1 style={{ fontSize: '28px', fontWeight: '700', textAlign: 'center', marginBottom: '8px' }}>{t('auth.createAccount')}</h1>
          <p style={{ color: 'var(--color-text-muted)', textAlign: 'center', marginBottom: '32px' }}>{t('auth.registerSubtitle')}</p>

          {/* Google Sign Up - only if client ID is configured */}
          {GOOGLE_CLIENT_ID && (
            <>
              <div style={{ marginBottom: '32px' }}>
                <div style={{ display: 'flex', justifyContent: 'center' }}>
                  <GoogleLogin
                    onSuccess={handleGoogleSuccess}
                    onError={handleGoogleError}
                    theme="filled_black"
                    size="large"
                    width="352"
                    text="signup_with"
                    shape="rectangular"
                  />
                </div>
              </div>

              {/* Divider */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '32px' }}>
                <div style={{ flex: 1, height: '1px', background: 'var(--color-border)' }} />
                <span style={{ color: 'var(--color-text-muted)', fontSize: '14px' }}>{t('auth.orRegisterWith')}</span>
                <div style={{ flex: 1, height: '1px', background: 'var(--color-border)' }} />
              </div>
            </>
          )}

          {error && (
            <div style={{ marginBottom: '24px', padding: '16px', borderRadius: '12px', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.2)', color: 'var(--color-danger)', fontSize: '14px' }}>
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit(onSubmit)}>
            {/* Honeypot — gizli alan; gerçek kullanıcı görmez/doldurmaz, bot doldurur */}
            <input
              type="text"
              tabIndex={-1}
              autoComplete="off"
              aria-hidden="true"
              {...register('website')}
              style={{ position: 'absolute', left: '-9999px', top: '-9999px', width: '1px', height: '1px', opacity: 0 }}
            />

            {/* Name */}
            <div style={{ marginBottom: '24px' }}>
              <label style={{ display: 'block', fontSize: '14px', fontWeight: '500', marginBottom: '8px' }}>{t('auth.fullName')}</label>
              <div style={{ position: 'relative' }}>
                <User style={{ position: 'absolute', left: '16px', top: '50%', transform: 'translateY(-50%)', width: '20px', height: '20px', color: 'var(--color-text-muted)' }} />
                <input
                  type="text"
                  {...register('name', {
                    required: 'Please enter your name.',
                    validate: (value) => {
                      const s = (value || '').trim()
                      if (s.length < 2) return 'Please enter your name.'
                      if (s.length > 50) return 'Name is too long (max 50 characters).'
                      if (NAME_BANNED.test(s)) return 'Name contains invalid characters.'
                      return true
                    },
                  })}
                  className="input"
                  style={{ paddingLeft: '48px' }}
                  placeholder={t('auth.namePlaceholder')}
                />
              </div>
              {errors.name && <p style={{ marginTop: '8px', fontSize: '13px', color: 'var(--color-danger)' }}>{errors.name.message}</p>}
            </div>

            {/* Email */}
            <div style={{ marginBottom: '24px' }}>
              <label style={{ display: 'block', fontSize: '14px', fontWeight: '500', marginBottom: '8px' }}>{t('auth.email')}</label>
              <div style={{ position: 'relative' }}>
                <Mail style={{ position: 'absolute', left: '16px', top: '50%', transform: 'translateY(-50%)', width: '20px', height: '20px', color: 'var(--color-text-muted)' }} />
                <input type="email" {...register('email', { required: true })} className="input" style={{ paddingLeft: '48px' }} placeholder={t('auth.emailPlaceholder')} />
              </div>
              {errors.email && <p style={{ marginTop: '8px', fontSize: '13px', color: 'var(--color-danger)' }}>{errors.email.message}</p>}
            </div>

            {/* Password */}
            <div style={{ marginBottom: '32px' }}>
              <label style={{ display: 'block', fontSize: '14px', fontWeight: '500', marginBottom: '8px' }}>{t('auth.password')}</label>
              <div style={{ position: 'relative' }}>
                <Lock style={{ position: 'absolute', left: '16px', top: '50%', transform: 'translateY(-50%)', width: '20px', height: '20px', color: 'var(--color-text-muted)' }} />
                <input type={showPassword ? 'text' : 'password'} {...register('password', { required: true, minLength: 8 })} className="input" style={{ paddingLeft: '48px', paddingRight: '48px' }} placeholder="••••••••" />
                <button type="button" onClick={() => setShowPassword(!showPassword)}
                  style={{ position: 'absolute', right: '16px', top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--color-text-muted)' }}>
                  {showPassword ? <EyeOff style={{ width: '20px', height: '20px' }} /> : <Eye style={{ width: '20px', height: '20px' }} />}
                </button>
              </div>
              {errors.password && <p style={{ marginTop: '8px', fontSize: '13px', color: 'var(--color-danger)' }}>{errors.password.message}</p>}
              
              {password && (
                <div style={{ marginTop: '16px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {passwordRequirements.map((req, i) => (
                    <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <div style={{ width: '20px', height: '20px', borderRadius: '50%', background: req.met ? 'var(--color-success)' : 'var(--color-bg-tertiary)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        {req.met && <Check style={{ width: '12px', height: '12px', color: 'white' }} />}
                      </div>
                      <span style={{ fontSize: '13px', color: req.met ? 'var(--color-success)' : 'var(--color-text-muted)' }}>{req.text}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Cloudflare Turnstile (oturum #9.0) */}
            <TurnstileWidget ref={turnstileRef} onVerify={setTurnstileToken} />

            {/* Submit */}
            <button type="submit" disabled={isLoading || (turnstileEnabled && !turnstileToken)} className="btn btn-primary" style={{ width: '100%', padding: '16px', fontSize: '16px' }}>
              {isLoading ? (
                <><Loader2 style={{ width: '20px', height: '20px', animation: 'spin 1s linear infinite' }} /> {t('auth.creatingAccount')}</>
              ) : (
                <>{t('auth.createAccountBtn')} <ArrowRight style={{ width: '20px', height: '20px' }} /></>
              )}
            </button>
          </form>

          <p style={{ marginTop: '32px', textAlign: 'center', color: 'var(--color-text-muted)', fontSize: '14px' }}>
            {t('auth.haveAccount')}{' '}
            <Link to="/login" style={{ color: 'var(--color-accent-cyan)', textDecoration: 'none', fontWeight: '500' }}>{t('auth.signInLink')}</Link>
          </p>
        </div>
      </motion.div>
    </div>
  )
}

export default Register
