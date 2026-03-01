import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useTranslation } from 'react-i18next'
import { TestTube, Swords, BarChart3, Globe, ArrowRight, Sparkles, Users } from 'lucide-react'
import PublicNavbar from '../components/layout/PublicNavbar'
import Footer from '../components/layout/Footer'

function Landing() {
  const { t } = useTranslation()

  const features = [
    { icon: TestTube, title: t('landing.campaignTesting'), description: t('landing.campaignTestingDesc') },
    { icon: Swords, title: t('landing.abComparison'), description: t('landing.abComparisonDesc') },
    { icon: BarChart3, title: t('landing.segmentAnalysis'), description: t('landing.segmentAnalysisDesc') },
    { icon: Globe, title: t('landing.multiRegion'), description: t('landing.multiRegionDesc') },
  ]

  const steps = [
    { num: 1, title: t('landing.step1Title'), desc: t('landing.step1Desc') },
    { num: 2, title: t('landing.step2Title'), desc: t('landing.step2Desc') },
    { num: 3, title: t('landing.step3Title'), desc: t('landing.step3Desc') },
    { num: 4, title: t('landing.step4Title'), desc: t('landing.step4Desc') },
  ]

  const stats = [
    { value: '1M+', label: t('landing.syntheticPersonas') },
    { value: '4', label: t('landing.globalRegions') },
    { value: '<30s', label: t('landing.resultsTime') },
    { value: '95%', label: t('landing.accuracyRate') },
  ]

  const testimonials = [
    { quote: t('landing.testimonial1'), author: t('landing.testimonial1Author'), role: t('landing.testimonial1Role') },
    { quote: t('landing.testimonial2'), author: t('landing.testimonial2Author'), role: t('landing.testimonial2Role') },
    { quote: t('landing.testimonial3'), author: t('landing.testimonial3Author'), role: t('landing.testimonial3Role') },
  ]

  return (
    <div style={{ minHeight: '100vh', backgroundColor: 'var(--color-bg-primary)' }}>
      <PublicNavbar />

      {/* Hero Section */}
      <section className="hero-gradient hero-section" style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '120px 20px 80px 20px' }}>
        <div style={{ width: '100%', maxWidth: '900px', margin: '0 auto', textAlign: 'center' }}>
          
          {/* Badge */}
          <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}
            style={{ display: 'flex', justifyContent: 'center', marginBottom: '36px' }}>
            <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '10px 20px', borderRadius: '9999px', background: 'rgba(6, 182, 212, 0.1)', border: '1px solid rgba(6, 182, 212, 0.2)' }}>
              <Sparkles style={{ width: '18px', height: '18px', color: 'var(--color-accent-cyan)' }} />
              <span style={{ fontSize: '14px', fontWeight: '500', color: 'var(--color-accent-cyan)' }}>{t('landing.badge')}</span>
            </div>
          </motion.div>

          {/* Main Title */}
          <motion.h1 initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.1 }} 
            style={{ fontSize: 'clamp(36px, 7vw, 76px)', fontWeight: '700', marginBottom: '32px', lineHeight: '1.1' }}>
            {t('landing.heroTitle1')}<br />
            <span className="gradient-text">{t('landing.heroTitle2')}</span>
          </motion.h1>

          {/* Subtitle */}
          <motion.p initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.2 }} 
            style={{ fontSize: 'clamp(16px, 2.5vw, 22px)', color: 'var(--color-text-secondary)', maxWidth: '700px', margin: '0 auto 48px auto', lineHeight: '1.6' }}>
            {t('landing.heroSubtitle')}
          </motion.p>

          {/* Buttons */}
          <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.3 }} 
            className="hero-buttons" style={{ display: 'flex', flexWrap: 'wrap', gap: '16px', justifyContent: 'center', marginBottom: '64px' }}>
            <Link to="/register" className="btn btn-primary" style={{ fontSize: '16px', padding: '16px 32px' }}>
              {t('landing.startFreeTrial')} <ArrowRight style={{ width: '18px', height: '18px' }} />
            </Link>
            <a href="#how-it-works" className="btn btn-secondary" style={{ fontSize: '16px', padding: '16px 32px' }}>
              {t('landing.seeHowItWorks')}
            </a>
          </motion.div>

          {/* Stats */}
          <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.4 }} 
            style={{ width: '100%', maxWidth: '800px', margin: '0 auto' }}>
            <div className="grid-stats" style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '32px' }}>
              {stats.map((stat, i) => (
                <div key={i} style={{ textAlign: 'center' }}>
                  <div className="gradient-text" style={{ fontSize: 'clamp(28px, 4vw, 44px)', fontWeight: '700', marginBottom: '8px' }}>{stat.value}</div>
                  <div style={{ fontSize: '13px', color: 'var(--color-text-muted)' }}>{stat.label}</div>
                </div>
              ))}
            </div>
          </motion.div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="section-lg" style={{ padding: '120px 20px', scrollMarginTop: '80px' }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
          <div className="section-header-mb" style={{ textAlign: 'center', marginBottom: '72px' }}>
            <motion.h2 initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
              style={{ fontSize: 'clamp(30px, 5vw, 52px)', fontWeight: '700', marginBottom: '20px' }}>
              {t('landing.featuresTitle1')} <span className="gradient-text">{t('landing.featuresTitle2')}</span>
            </motion.h2>
            <motion.p initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: 0.1 }}
              style={{ fontSize: 'clamp(16px, 2vw, 20px)', color: 'var(--color-text-secondary)', maxWidth: '600px', margin: '0 auto' }}>
              {t('landing.featuresSubtitle')}
            </motion.p>
          </div>

          <div className="grid-features" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '24px' }}>
            {features.map((feature, i) => {
              const Icon = feature.icon
              return (
                <motion.div key={i} initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.1 }}
                  className="feature-card" style={{ padding: '32px' }}>
                  <div className="gradient-bg" style={{ width: '56px', height: '56px', borderRadius: '14px', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '20px' }}>
                    <Icon style={{ width: '28px', height: '28px', color: 'white' }} />
                  </div>
                  <h3 style={{ fontSize: '20px', fontWeight: '700', marginBottom: '12px' }}>{feature.title}</h3>
                  <p style={{ fontSize: '15px', color: 'var(--color-text-muted)', lineHeight: '1.7' }}>{feature.description}</p>
                </motion.div>
              )
            })}
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section id="how-it-works" className="section-lg" style={{ padding: '120px 20px', backgroundColor: 'var(--color-bg-secondary)', scrollMarginTop: '80px' }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
          <div className="section-header-mb" style={{ textAlign: 'center', marginBottom: '72px' }}>
            <motion.h2 initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
              style={{ fontSize: 'clamp(30px, 5vw, 52px)', fontWeight: '700', marginBottom: '20px' }}>
              {t('landing.howItWorksTitle')} <span className="gradient-text">{t('landing.howItWorksTitle2')}</span>
            </motion.h2>
            <motion.p initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: 0.1 }}
              style={{ fontSize: 'clamp(16px, 2vw, 20px)', color: 'var(--color-text-secondary)' }}>
              {t('landing.howItWorksSubtitle')}
            </motion.p>
          </div>

          <div className="grid-steps" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '48px' }}>
            {steps.map((step, i) => (
              <motion.div key={i} initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.15 }}
                style={{ textAlign: 'center' }}>
                <div className="gradient-bg" style={{ width: '72px', height: '72px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 24px auto', fontSize: '30px', fontWeight: '700', color: 'white', boxShadow: '0 16px 32px rgba(6, 182, 212, 0.2)' }}>
                  {step.num}
                </div>
                <h3 style={{ fontSize: '20px', fontWeight: '700', marginBottom: '12px' }}>{step.title}</h3>
                <p style={{ fontSize: '15px', color: 'var(--color-text-muted)', lineHeight: '1.7' }}>{step.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonials Section */}
      <section className="section-lg" style={{ padding: '120px 20px' }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
          <div className="section-header-mb" style={{ textAlign: 'center', marginBottom: '60px' }}>
            <motion.h2 initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
              style={{ fontSize: 'clamp(30px, 5vw, 52px)', fontWeight: '700', marginBottom: '20px' }}>
              {t('landing.trustedBy')} <span className="gradient-text">{t('landing.industryLeaders')}</span>
            </motion.h2>
          </div>

          <div className="grid-testimonials" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '24px' }}>
            {testimonials.map((tst, i) => (
              <motion.div key={i} initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.1 }}
                className="card" style={{ padding: '32px' }}>
                <p style={{ fontSize: '16px', color: 'var(--color-text-secondary)', marginBottom: '24px', lineHeight: '1.7' }}>"{tst.quote}"</p>
                <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                  <div className="gradient-bg" style={{ width: '44px', height: '44px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                    <Users style={{ width: '22px', height: '22px', color: 'white' }} />
                  </div>
                  <div>
                    <div style={{ fontWeight: '600', fontSize: '15px' }}>{tst.author}</div>
                    <div style={{ fontSize: '13px', color: 'var(--color-text-muted)' }}>{tst.role}</div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="section-lg" style={{ padding: '80px 20px 120px 20px' }}>
        <div style={{ maxWidth: '900px', margin: '0 auto' }}>
          <motion.div initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
            className="gradient-border cta-inner" style={{ padding: '64px 32px', textAlign: 'center' }}>
            <h2 style={{ fontSize: 'clamp(28px, 4vw, 44px)', fontWeight: '700', marginBottom: '20px' }}>{t('landing.readyToTest')}</h2>
            <p style={{ fontSize: 'clamp(16px, 2vw, 20px)', color: 'var(--color-text-secondary)', maxWidth: '500px', margin: '0 auto 36px auto', lineHeight: '1.6' }}>
              {t('landing.ctaSubtitle')}
            </p>
            <Link to="/register" className="btn btn-primary" style={{ fontSize: '16px', padding: '16px 32px' }}>
              {t('landing.getStartedFree')} <ArrowRight style={{ width: '18px', height: '18px' }} />
            </Link>
          </motion.div>
        </div>
      </section>

      <Footer />
    </div>
  )
}

export default Landing
