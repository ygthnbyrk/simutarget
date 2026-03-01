import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useTranslation } from 'react-i18next'
import { Check, X, ArrowRight, Zap, Mail } from 'lucide-react'
import PublicNavbar from '../components/layout/PublicNavbar'
import Footer from '../components/layout/Footer'
import useAuthStore from '../stores/authStore'
import useCreditStore from '../stores/creditStore'

function Pricing() {
  const [billingPeriod, setBillingPeriod] = useState('monthly')
  const { isAuthenticated } = useAuthStore()
  const { plans, fetchPlans, subscribe } = useCreditStore()
  const navigate = useNavigate()
  const { t } = useTranslation()

  useEffect(() => { fetchPlans() }, [])

  const allFeatures = [
    { name: t('pricing.monthlyCredits'), disposable: '5', starter: '50', pro: '200', business: '600', enterprise: '2000+' },
    { name: t('pricing.singleCampaignTest'), disposable: true, starter: true, pro: true, business: true, enterprise: true },
    { name: t('pricing.regionSelection'), disposable: true, starter: true, pro: true, business: true, enterprise: true },
    { name: t('pricing.basicDemographics'), disposable: true, starter: true, pro: true, business: true, enterprise: true },
    { name: t('pricing.onScreenResults'), disposable: true, starter: true, pro: true, business: true, enterprise: true },
    { name: t('pricing.abComparison'), disposable: false, starter: false, pro: true, business: true, enterprise: true },
    { name: t('pricing.advancedFilters'), disposable: false, starter: false, pro: true, business: true, enterprise: true },
    { name: t('pricing.pdfExport'), disposable: false, starter: false, pro: true, business: true, enterprise: true },
    { name: t('pricing.multiCompare'), disposable: false, starter: false, pro: false, business: true, enterprise: true },
    { name: t('pricing.incomeEducationFilters'), disposable: false, starter: false, pro: false, business: true, enterprise: true },
    { name: t('pricing.prioritySupport'), disposable: false, starter: false, pro: false, business: true, enterprise: true },
    { name: t('pricing.customProfiles'), disposable: false, starter: false, pro: false, business: false, enterprise: true },
    { name: t('pricing.unlimitedComparisons'), disposable: false, starter: false, pro: false, business: false, enterprise: true },
    { name: t('pricing.apiAccess'), disposable: false, starter: false, pro: false, business: false, enterprise: true },
    { name: t('pricing.dedicatedManager'), disposable: false, starter: false, pro: false, business: false, enterprise: true },
  ]

  const planData = [
    { slug: 'starter', name: 'Starter', price: 49.99, description: t('pricing.starterDesc'), color: '#6B7280' },
    { slug: 'pro', name: 'Pro', price: 149.99, description: t('pricing.proDesc'), popular: true, color: '#06B6D4' },
    { slug: 'business', name: 'Business', price: 399.99, description: t('pricing.businessDesc'), color: '#8B5CF6' },
    { slug: 'enterprise', name: 'Enterprise', price: null, description: t('pricing.enterpriseDesc'), color: '#F59E0B', isCustom: true },
  ]

  const tablePlans = [
    { slug: 'disposable', name: 'Disposable', price: 4.99, isCustom: false },
    ...planData,
  ]

  const handleSelectPlan = async (plan) => {
    if (plan.isCustom) { window.location.href = 'mailto:contact@simutarget.ai'; return }
    if (!isAuthenticated) { navigate('/register'); return }
    const result = await subscribe(plan.slug)
    if (result.success) navigate('/dashboard')
  }

  const getPrice = (price) => {
    if (price === null) return null
    return billingPeriod === 'yearly' ? (price * 12 * 0.8).toFixed(0) : price
  }

  return (
    <div style={{ minHeight: '100vh', backgroundColor: 'var(--color-bg-primary)' }}>
      <PublicNavbar />

      {/* Hero */}
      <section style={{ padding: '140px 20px 80px 20px' }}>
        <div style={{ maxWidth: '900px', margin: '0 auto', textAlign: 'center' }}>
          <motion.h1 initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} 
            style={{ fontSize: 'clamp(36px, 7vw, 68px)', fontWeight: '700', marginBottom: '24px', lineHeight: '1.1' }}>
            {t('pricing.title1')} <span className="gradient-text">{t('pricing.title2')}</span>
          </motion.h1>
          
          <motion.p initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
            style={{ fontSize: 'clamp(16px, 2.5vw, 20px)', color: 'var(--color-text-secondary)', maxWidth: '550px', margin: '0 auto 48px auto', lineHeight: '1.6' }}>
            {t('pricing.subtitle')}
          </motion.p>

          {/* Billing Toggle */}
          <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}
            className="billing-toggle"
            style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', padding: '6px', borderRadius: '14px', background: 'var(--color-bg-secondary)', border: '1px solid var(--color-border)' }}>
            <button onClick={() => setBillingPeriod('monthly')} 
              style={{ padding: '14px 28px', borderRadius: '10px', fontSize: '15px', fontWeight: '600', border: 'none', cursor: 'pointer', transition: 'all 0.2s',
                background: billingPeriod === 'monthly' ? 'linear-gradient(135deg, var(--color-accent-cyan), var(--color-accent-purple))' : 'transparent',
                color: billingPeriod === 'monthly' ? 'white' : 'var(--color-text-secondary)' }}>
              {t('pricing.monthly')}
            </button>
            <button onClick={() => setBillingPeriod('yearly')} 
              style={{ padding: '14px 28px', borderRadius: '10px', fontSize: '15px', fontWeight: '600', border: 'none', cursor: 'pointer', transition: 'all 0.2s',
                background: billingPeriod === 'yearly' ? 'linear-gradient(135deg, var(--color-accent-cyan), var(--color-accent-purple))' : 'transparent',
                color: billingPeriod === 'yearly' ? 'white' : 'var(--color-text-secondary)' }}>
              {t('pricing.yearly')} <span style={{ color: billingPeriod === 'yearly' ? 'white' : 'var(--color-success)', marginLeft: '6px', fontWeight: '700' }}>-20%</span>
            </button>
          </motion.div>
        </div>
      </section>

      {/* Disposable */}
      <section style={{ padding: '0 20px 48px 20px' }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
          <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}
            className="disposable-card"
            style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '20px', padding: '28px 32px', borderRadius: '18px', background: 'linear-gradient(135deg, rgba(107, 114, 128, 0.1), rgba(107, 114, 128, 0.05))', border: '1px solid var(--color-border)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
              <div style={{ width: '44px', height: '44px', borderRadius: '12px', background: 'rgba(107, 114, 128, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                <Zap style={{ width: '22px', height: '22px', color: '#9CA3AF' }} />
              </div>
              <div>
                <div style={{ fontSize: '18px', fontWeight: '700', marginBottom: '2px' }}>Disposable</div>
                <div style={{ fontSize: '14px', color: 'var(--color-text-muted)' }}>{t('pricing.disposableDesc')}</div>
              </div>
            </div>
            <div className="disposable-inner" style={{ display: 'flex', alignItems: 'center', gap: '28px' }}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '13px', color: 'var(--color-text-muted)', marginBottom: '2px' }}>{t('pricing.monthlyCredits')}</div>
                <div style={{ fontSize: '18px', fontWeight: '700', color: 'var(--color-accent-cyan)' }}>5</div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px' }}>
                  <span style={{ fontSize: '32px', fontWeight: '800' }}>$4.99</span>
                  <span style={{ fontSize: '13px', color: 'var(--color-text-muted)' }}>{t('pricing.perTest')}</span>
                </div>
              </div>
              <button onClick={() => handleSelectPlan({ slug: 'disposable', isCustom: false })}
                className="btn btn-primary" style={{ padding: '12px 28px', fontSize: '14px', fontWeight: '600', borderRadius: '10px', display: 'flex', alignItems: 'center', gap: '8px', whiteSpace: 'nowrap' }}>
                {t('pricing.getStarted')} <ArrowRight style={{ width: '16px', height: '16px' }} />
              </button>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Pricing Cards */}
      <section style={{ padding: '0 20px 100px 20px' }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
          <div className="grid-pricing" style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '24px' }}>
            {planData.map((plan, i) => (
              <motion.div key={plan.slug} initial={{ opacity: 0, y: 40 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.1 }}
                style={{
                  position: 'relative', background: 'var(--color-bg-card)',
                  border: plan.popular ? '3px solid var(--color-accent-cyan)' : '1px solid var(--color-border)',
                  borderRadius: '24px', padding: '40px 28px',
                  transform: plan.popular ? 'scale(1.03)' : 'scale(1)',
                  boxShadow: plan.popular ? '0 24px 48px rgba(6, 182, 212, 0.15)' : '0 8px 32px rgba(0,0,0,0.1)',
                  zIndex: plan.popular ? 10 : 1
                }}>
                {plan.popular && (
                  <div style={{ position: 'absolute', top: '-16px', left: '50%', transform: 'translateX(-50%)',
                    background: 'linear-gradient(135deg, var(--color-accent-cyan), var(--color-accent-purple))',
                    padding: '8px 24px', borderRadius: '20px', fontSize: '13px', fontWeight: '700', color: 'white',
                    display: 'flex', alignItems: 'center', gap: '6px', whiteSpace: 'nowrap' }}>
                    <Zap style={{ width: '14px', height: '14px' }} /> {t('pricing.mostPopular')}
                  </div>
                )}

                <div style={{ textAlign: 'center', marginBottom: '32px', paddingTop: plan.popular ? '8px' : '0' }}>
                  <div style={{ width: '48px', height: '48px', borderRadius: '14px', background: `${plan.color}20`, display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px auto' }}>
                    <Zap style={{ width: '24px', height: '24px', color: plan.color }} />
                  </div>
                  <h3 style={{ fontSize: '24px', fontWeight: '700', marginBottom: '6px' }}>{plan.name}</h3>
                  <p style={{ fontSize: '14px', color: 'var(--color-text-muted)', marginBottom: '24px', minHeight: '40px' }}>{plan.description}</p>
                  
                  {plan.isCustom ? (
                    <div style={{ fontSize: '28px', fontWeight: '800', lineHeight: 1 }}>{t('pricing.customPricing')}</div>
                  ) : (
                    <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'center', gap: '4px' }}>
                      <span style={{ fontSize: '48px', fontWeight: '800', lineHeight: 1 }}>${getPrice(plan.price)}</span>
                      <span style={{ fontSize: '16px', color: 'var(--color-text-muted)' }}>{billingPeriod === 'yearly' ? t('pricing.perYear') : t('pricing.perMonth')}</span>
                    </div>
                  )}
                </div>

                <button onClick={() => handleSelectPlan(plan)}
                  className="btn btn-primary" style={{ width: '100%', padding: '16px', fontSize: '15px', fontWeight: '600', borderRadius: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
                  {plan.isCustom ? (<>{t('pricing.contactUs')} <Mail style={{ width: '18px', height: '18px' }} /></>) : (<>{t('pricing.getStarted')} <ArrowRight style={{ width: '18px', height: '18px' }} /></>)}
                </button>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Feature Comparison Table */}
      <section className="section-lg" style={{ padding: '100px 20px 120px 20px', background: 'var(--color-bg-secondary)' }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
          <div className="section-header-mb" style={{ textAlign: 'center', marginBottom: '60px' }}>
            <motion.h2 initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
              style={{ fontSize: 'clamp(30px, 5vw, 48px)', fontWeight: '700', marginBottom: '16px' }}>
              {t('pricing.compareAll')} <span className="gradient-text">{t('pricing.allFeatures')}</span>
            </motion.h2>
            <motion.p initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: 0.1 }}
              style={{ fontSize: '18px', color: 'var(--color-text-secondary)' }}>
              {t('pricing.seeIncluded')}
            </motion.p>
          </div>

          <motion.div initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
            className="comparison-scroll" style={{ background: 'var(--color-bg-card)', borderRadius: '20px', overflow: 'hidden', border: '1px solid var(--color-border)' }}>
            <div style={{ minWidth: '800px' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 1fr 1fr 1fr', background: 'var(--color-bg-tertiary)', borderBottom: '2px solid var(--color-border)' }}>
                <div style={{ padding: '24px 28px', fontWeight: '700', fontSize: '16px' }}>{t('pricing.features')}</div>
                {tablePlans.map((plan) => (
                  <div key={plan.slug} style={{ padding: '24px 12px', textAlign: 'center', fontWeight: '700', fontSize: '14px',
                    background: plan.popular ? 'rgba(6, 182, 212, 0.1)' : 'transparent', borderLeft: '1px solid var(--color-border)' }}>
                    {plan.name}
                    <div style={{ fontSize: '12px', color: 'var(--color-text-muted)', fontWeight: '400', marginTop: '4px' }}>
                      {plan.isCustom ? t('pricing.customPricing') : `$${plan.price}${t('pricing.perMonth')}`}
                    </div>
                  </div>
                ))}
              </div>

              {allFeatures.map((feature, i) => (
                <div key={i} style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 1fr 1fr 1fr',
                  borderBottom: i < allFeatures.length - 1 ? '1px solid var(--color-border)' : 'none' }}>
                  <div style={{ padding: '18px 28px', fontSize: '14px', color: 'var(--color-text-secondary)', display: 'flex', alignItems: 'center' }}>{feature.name}</div>
                  {tablePlans.map((plan) => {
                    const value = feature[plan.slug]
                    return (
                      <div key={plan.slug} style={{ padding: '18px 10px', textAlign: 'center', display: 'flex', alignItems: 'center', justifyContent: 'center',
                        background: plan.popular ? 'rgba(6, 182, 212, 0.05)' : 'transparent', borderLeft: '1px solid var(--color-border)' }}>
                        {typeof value === 'string' ? (
                          <span style={{ fontWeight: '700', fontSize: '15px', color: 'var(--color-accent-cyan)' }}>{value}</span>
                        ) : value ? (
                          <div style={{ width: '28px', height: '28px', borderRadius: '50%', background: 'rgba(16, 185, 129, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                            <Check style={{ width: '16px', height: '16px', color: 'var(--color-success)' }} />
                          </div>
                        ) : (
                          <div style={{ width: '28px', height: '28px', borderRadius: '50%', background: 'rgba(107, 114, 128, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                            <X style={{ width: '16px', height: '16px', color: 'var(--color-text-muted)', opacity: 0.4 }} />
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>
              ))}
            </div>
          </motion.div>
        </div>
      </section>

      {/* Contact CTA */}
      <section className="section-lg" style={{ padding: '100px 20px' }}>
        <div style={{ maxWidth: '800px', margin: '0 auto', textAlign: 'center' }}>
          <motion.div initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
            className="gradient-border cta-inner" style={{ padding: '64px 40px' }}>
            <Zap style={{ width: '48px', height: '48px', color: 'var(--color-accent-cyan)', margin: '0 auto 24px auto' }} />
            <h2 style={{ fontSize: 'clamp(24px, 4vw, 36px)', fontWeight: '700', marginBottom: '16px' }}>{t('pricing.needCustom')}</h2>
            <p style={{ fontSize: '18px', color: 'var(--color-text-secondary)', marginBottom: '32px', maxWidth: '450px', margin: '0 auto 32px auto', lineHeight: '1.6' }}>
              {t('pricing.contactSubtitle')}
            </p>
            <a href="mailto:contact@simutarget.ai" className="btn btn-primary" style={{ fontSize: '16px', padding: '16px 40px' }}>
              {t('pricing.contactSales')} <ArrowRight style={{ width: '18px', height: '18px' }} />
            </a>
          </motion.div>
        </div>
      </section>

      <Footer />
    </div>
  )
}

export default Pricing
