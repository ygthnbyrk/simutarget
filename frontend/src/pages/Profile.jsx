import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { useTranslation } from 'react-i18next'
import { User, Mail, CreditCard, Calendar, ArrowRight, Check, X, Loader2, ExternalLink, AlertTriangle } from 'lucide-react'
import DashboardLayout from '../components/layout/DashboardLayout'
import useAuthStore from '../stores/authStore'
import useCreditStore from '../stores/creditStore'

function Profile() {
  const { user } = useAuthStore()
  const {
    balance,
    subscription,
    plans,
    fetchPlans,
    fetchBalance,
    fetchSubscription,
    changePlan,
    subscribe,
    openCustomerPortal,
    isLoading,
  } = useCreditStore()
  const [selectedPlan, setSelectedPlan] = useState(null)
  const [showModal, setShowModal] = useState(false)
  const [showCancelModal, setShowCancelModal] = useState(false)
  const [showPlanChangeWarning, setShowPlanChangeWarning] = useState(false)
  const [checkoutMessage, setCheckoutMessage] = useState(null) // 'success' | 'cancelled' | null
  const { t } = useTranslation()

  useEffect(() => {
    fetchPlans()
    fetchSubscription()
    fetchBalance()

    // ?checkout=success ile dönen kullanıcı için: 2 saniye sonra refresh
    // (LS webhook'un DB'yi güncellemesi için zaman bırak)
    const params = new URLSearchParams(window.location.search)
    if (params.get('checkout') === 'success') {
      setCheckoutMessage('success')
      // Webhook gecikme buffer'ı
      const t1 = setTimeout(() => {
        fetchSubscription()
        fetchBalance()
      }, 2000)
      // URL'i temizle (geri tuşunda tekrar tetiklenmesin)
      const url = new URL(window.location.href)
      url.searchParams.delete('checkout')
      window.history.replaceState({}, '', url.toString())
      return () => clearTimeout(t1)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const allFeatures = [
    { name: t('profile.monthlyCredits'), disposable: '5', starter: '50', pro: '200', business: '600', enterprise: '2000' },
    { name: t('profile.singleCampaignTest'), disposable: true, starter: true, pro: true, business: true, enterprise: true },
    { name: t('profile.regionSelection'), disposable: true, starter: true, pro: true, business: true, enterprise: true },
    { name: t('profile.abComparison'), disposable: false, starter: false, pro: true, business: true, enterprise: true },
    { name: t('profile.multiCompare'), disposable: false, starter: false, pro: false, business: true, enterprise: true },
    { name: t('profile.pdfExport'), disposable: false, starter: false, pro: true, business: true, enterprise: true },
    { name: t('profile.apiAccess'), disposable: false, starter: false, pro: false, business: false, enterprise: true },
  ]

  const defaultPlans = [
    { slug: 'disposable', name: 'Disposable', price_monthly: 4.99, credits_monthly: 5 },
    { slug: 'starter', name: 'Starter', price_monthly: 49.99, credits_monthly: 50 },
    { slug: 'pro', name: 'Pro', price_monthly: 149.99, credits_monthly: 200 },
    { slug: 'business', name: 'Business', price_monthly: 399.99, credits_monthly: 600 },
    { slug: 'enterprise', name: 'Enterprise', price_monthly: null, credits_monthly: 2000 },
  ]

  // Kullanıcının zaten aboneliği varsa ve yeni "subscription" planı seçtiyse uyarı göster
  const handlePlanSelect = (planSlug) => {
    setSelectedPlan(planSlug)
    // Aboneliği var ve seçtiği plan disposable değilse (yani başka bir abonelik) → uyarı modal
    if (subscription && planSlug !== 'disposable' && subscription.plan_slug !== planSlug) {
      setShowPlanChangeWarning(true)
    } else {
      setShowModal(true)
    }
  }

  const handleUpgrade = async () => {
    if (!selectedPlan) return
    try {
      // creditStore.subscribe ve changePlan ikisi de aynı LS checkout akışı.
      // İkisi de window.LemonSqueezy.Url.Open() ile overlay açar.
      let result
      if (!subscription) {
        result = await subscribe(selectedPlan)
      } else {
        result = await changePlan(selectedPlan)
      }
      if (result?.success) {
        // Overlay açıldı, modal'ı kapat (overlay'in arkasında durması UX'i bozar)
        setShowModal(false)
        setSelectedPlan(null)
      }
      // success=false ise creditStore.error set edildi, modal açık kalır
    } catch (err) {
      console.error('Checkout error:', err)
    }
  }

  // "Önce mevcut aboneliği iptal et" → LS portal aç
  const handleManageSubscription = async () => {
    setShowPlanChangeWarning(false)
    setShowCancelModal(false)
    await openCustomerPortal()
  }

  return (
    <DashboardLayout>
      <div style={{ maxWidth: '1000px', margin: '0 auto' }}>
        <div style={{ marginBottom: '48px' }}>
          <h1 style={{ fontSize: '32px', fontWeight: '700', marginBottom: '8px' }}>{t('profile.title')}</h1>
          <p style={{ fontSize: '16px', color: 'var(--color-text-muted)' }}>{t('profile.subtitle')}</p>
        </div>

        {/* Checkout success banner */}
        {checkoutMessage === 'success' && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            style={{
              padding: '16px 24px',
              marginBottom: '24px',
              borderRadius: '12px',
              background: 'rgba(34, 197, 94, 0.1)',
              border: '1px solid rgba(34, 197, 94, 0.3)',
              color: 'var(--color-success, #22c55e)',
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
            }}
          >
            <Check style={{ width: '20px', height: '20px' }} />
            <span>Ödeme başarılı! Aboneliğiniz birkaç saniye içinde aktifleşecek.</span>
            <button
              onClick={() => setCheckoutMessage(null)}
              style={{ marginLeft: 'auto', background: 'none', border: 'none', color: 'inherit', cursor: 'pointer' }}
            >
              <X style={{ width: '18px', height: '18px' }} />
            </button>
          </motion.div>
        )}

        {/* Account Info */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="card" style={{ padding: '32px', marginBottom: '32px' }}>
          <h2 style={{ fontSize: '20px', fontWeight: '600', marginBottom: '24px' }}>{t('profile.accountInfo')}</h2>
          <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
            <div className="gradient-bg" style={{ width: '72px', height: '72px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <User style={{ width: '36px', height: '36px', color: 'white' }} />
            </div>
            <div>
              <div style={{ fontSize: '24px', fontWeight: '600', marginBottom: '4px' }}>{user?.name || 'User'}</div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--color-text-muted)' }}>
                <Mail style={{ width: '18px', height: '18px' }} />
                <span>{user?.email || 'email@example.com'}</span>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Current Subscription */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="card" style={{ padding: '32px', marginBottom: '32px' }}>
          <h2 style={{ fontSize: '20px', fontWeight: '600', marginBottom: '24px' }}>{t('profile.currentSubscription')}</h2>
          <div className="grid-profile-sub" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
            <div style={{ padding: '24px', background: 'var(--color-bg-tertiary)', borderRadius: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--color-text-muted)', marginBottom: '8px' }}>
                <CreditCard style={{ width: '18px', height: '18px' }} />
                <span style={{ fontSize: '14px' }}>{t('profile.currentPlan')}</span>
              </div>
              <div className="gradient-text" style={{ fontSize: '28px', fontWeight: '700' }}>{subscription?.plan_name || t('dashboard.noSubscription')}</div>
            </div>
            <div style={{ padding: '24px', background: 'var(--color-bg-tertiary)', borderRadius: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--color-text-muted)', marginBottom: '8px' }}>
                <Calendar style={{ width: '18px', height: '18px' }} />
                <span style={{ fontSize: '14px' }}>{t('profile.creditsRemaining')}</span>
              </div>
              <div style={{ fontSize: '28px', fontWeight: '700' }}>{balance} <span style={{ fontSize: '16px', color: 'var(--color-text-muted)' }}>/ {subscription?.credits_monthly || 0}</span></div>
            </div>
          </div>
          {subscription && (
            <div style={{ marginTop: '20px', display: 'flex', gap: '12px', flexWrap: 'wrap', justifyContent: 'flex-end' }}>
              <button
                onClick={openCustomerPortal}
                disabled={isLoading}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  background: 'var(--color-bg-tertiary)',
                  border: '1px solid var(--color-border)',
                  color: 'var(--color-text-primary)',
                  fontSize: '14px',
                  cursor: 'pointer',
                  padding: '10px 16px',
                  borderRadius: '8px',
                  fontWeight: '500',
                }}
              >
                <ExternalLink style={{ width: '16px', height: '16px' }} />
                Manage Subscription
              </button>
            </div>
          )}
        </motion.div>

        {/* Plan Comparison */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="card" style={{ padding: '32px' }}>
          <h2 style={{ fontSize: '20px', fontWeight: '600', marginBottom: '24px' }}>{t('profile.comparePlans')}</h2>
          
          <div className="comparison-scroll" style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: '750px' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--color-border)' }}>
                  <th style={{ textAlign: 'left', padding: '16px', fontWeight: '600' }}>{t('profile.feature')}</th>
                  {defaultPlans.map(plan => (
                    <th key={plan.slug} style={{ textAlign: 'center', padding: '16px', fontWeight: '600', background: subscription?.plan_slug === plan.slug ? 'rgba(6, 182, 212, 0.1)' : 'transparent' }}>
                      {plan.name}
                      <div style={{ fontSize: '12px', color: 'var(--color-text-muted)', fontWeight: '400', marginTop: '4px' }}>{plan.price_monthly ? `$${plan.price_monthly}${t('pricing.perMonth')}` : t('pricing.contactUs')}</div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {allFeatures.map((feature, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid var(--color-border)' }}>
                    <td style={{ padding: '16px', fontSize: '14px', color: 'var(--color-text-secondary)' }}>{feature.name}</td>
                    {defaultPlans.map(plan => {
                      const value = feature[plan.slug]
                      return (
                        <td key={plan.slug} style={{ textAlign: 'center', padding: '16px', background: subscription?.plan_slug === plan.slug ? 'rgba(6, 182, 212, 0.05)' : 'transparent' }}>
                          {typeof value === 'string' ? (
                            <span style={{ fontWeight: '600', color: 'var(--color-accent-cyan)' }}>{value}</span>
                          ) : value ? (
                            <Check style={{ width: '20px', height: '20px', color: 'var(--color-success)', margin: '0 auto' }} />
                          ) : (
                            <X style={{ width: '20px', height: '20px', color: 'var(--color-text-muted)', opacity: 0.3, margin: '0 auto' }} />
                          )}
                        </td>
                      )
                    })}
                  </tr>
                ))}
                <tr>
                  <td></td>
                  {defaultPlans.map(plan => (
                    <td key={plan.slug} style={{ textAlign: 'center', padding: '16px' }}>
                      {subscription?.plan_slug === plan.slug ? (
                        <span style={{ padding: '8px 16px', borderRadius: '8px', background: 'rgba(6, 182, 212, 0.1)', color: 'var(--color-accent-cyan)', fontSize: '14px', fontWeight: '500' }}>{t('profile.current')}</span>
                      ) : plan.slug === 'enterprise' ? (
                        <button onClick={() => window.location.href = '/contact'} className="btn btn-secondary" style={{ padding: '8px 16px', fontSize: '14px' }}>
                          {t('pricing.contactUs')}
                        </button>
                      ) : (
                        <button onClick={() => handlePlanSelect(plan.slug)} className="btn btn-secondary" style={{ padding: '8px 16px', fontSize: '14px' }}>
                          {defaultPlans.findIndex(p => p.slug === plan.slug) > defaultPlans.findIndex(p => p.slug === subscription?.plan_slug) ? t('profile.upgrade') : t('profile.switch')}
                        </button>
                      )}
                    </td>
                  ))}
                </tr>
              </tbody>
            </table>
          </div>
        </motion.div>

        {/* Plan Selection Modal (LS Checkout açacak) */}
        {showModal && (
          <div style={{ position: 'fixed', inset: 0, zIndex: 100, display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'rgba(0,0,0,0.7)', padding: '24px' }}>
            <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="card" style={{ padding: '32px', maxWidth: '420px', width: '100%' }}>
              <h3 style={{ fontSize: '24px', fontWeight: '700', marginBottom: '16px' }}>
                {subscription ? t('profile.changePlan') : 'Subscribe'}
              </h3>
              <p style={{ color: 'var(--color-text-muted)', marginBottom: '8px', lineHeight: 1.6 }}>
                <strong style={{ color: 'var(--color-text-primary)' }}>
                  {selectedPlan?.charAt(0).toUpperCase() + selectedPlan?.slice(1)}
                </strong>{' '}
                planı için Lemon Squeezy güvenli ödeme sayfası açılacak.
              </p>
              <p style={{ color: 'var(--color-text-muted)', marginBottom: '24px', fontSize: '13px' }}>
                Kartınızla ödeme yaptıktan sonra otomatik olarak buraya döneceksiniz ve aboneliğiniz aktifleşecek.
              </p>
              <div style={{ display: 'flex', gap: '12px' }}>
                <button onClick={() => { setShowModal(false); setSelectedPlan(null) }} className="btn btn-secondary" style={{ flex: 1, padding: '14px' }}>
                  {t('common.cancel')}
                </button>
                <button onClick={handleUpgrade} disabled={isLoading} className="btn btn-primary" style={{ flex: 1, padding: '14px' }}>
                  {isLoading ? <Loader2 style={{ width: '18px', height: '18px', animation: 'spin 1s linear infinite' }} /> : 'Ödeme sayfasına git'}
                </button>
              </div>
            </motion.div>
          </div>
        )}

        {/* Plan Change Warning Modal (mevcut subscription var, başka subscription'a geçmek istiyor) */}
        {showPlanChangeWarning && (
          <div style={{ position: 'fixed', inset: 0, zIndex: 100, display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'rgba(0,0,0,0.7)', padding: '24px' }}>
            <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="card" style={{ padding: '32px', maxWidth: '460px', width: '100%' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
                <AlertTriangle style={{ width: '28px', height: '28px', color: '#f59e0b' }} />
                <h3 style={{ fontSize: '22px', fontWeight: '700', margin: 0 }}>Önce mevcut aboneliğinizi iptal edin</h3>
              </div>
              <p style={{ color: 'var(--color-text-muted)', marginBottom: '16px', lineHeight: 1.6 }}>
                Şu an <strong style={{ color: 'var(--color-text-primary)' }}>{subscription?.plan_name}</strong> aboneliğiniz aktif.
                Yeni bir plana geçmek için önce mevcut aboneliği iptal etmeniz gerekiyor —
                aksi halde iki abonelikten birden ücretlendirilirsiniz.
              </p>
              <p style={{ color: 'var(--color-text-muted)', marginBottom: '24px', fontSize: '13px', lineHeight: 1.6 }}>
                <strong style={{ color: 'var(--color-text-primary)' }}>Manage Subscription</strong> butonuna basarak Lemon Squeezy
                portalında aboneliğinizi iptal edin. İptal sonrası bu sayfaya dönüp yeni planı satın alabilirsiniz.
              </p>
              <div style={{ display: 'flex', gap: '12px' }}>
                <button onClick={() => { setShowPlanChangeWarning(false); setSelectedPlan(null) }} className="btn btn-secondary" style={{ flex: 1, padding: '14px' }}>
                  Vazgeç
                </button>
                <button onClick={handleManageSubscription} disabled={isLoading} className="btn btn-primary" style={{ flex: 1, padding: '14px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
                  {isLoading ? (
                    <Loader2 style={{ width: '18px', height: '18px', animation: 'spin 1s linear infinite' }} />
                  ) : (
                    <>
                      <ExternalLink style={{ width: '16px', height: '16px' }} />
                      Aboneliği Yönet
                    </>
                  )}
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </div>
    </DashboardLayout>
  )
}

export default Profile
