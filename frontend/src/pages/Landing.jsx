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
      <section className="hero-gradient" style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '0 24px' }}>
        <div style={{ width: '100%', maxWidth: '900px', margin: '0 auto', textAlign: 'center' }}>
          
          {/* Badge */}
          <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}
            style={{ display: 'flex', justifyContent: 'center', marginBottom: '48px' }}>
            <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '10px 20px', borderRadius: '9999px', background: 'rgba(6, 182, 212, 0.1)', border: '1px solid rgba(6, 182, 212, 0.2)' }}>
              <Sparkles style={{ width: '20px', height: '20px', color: 'var(--color-accent-cyan)' }} />
              <span style={{ fontSize: '14px', fontWeight: '500', color: 'var(--color-accent-cyan)' }}>{t('landing.badge')}</span>
            </div>
          </motion.div>

          {/* Main Title */}
          <motion.h1 initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.1 }} 
            style={{ fontSize: 'clamp(48px, 8vw, 80px)', fontWeight: '700', marginBottom: '60px', lineHeight: '1.1' }}>
            {t('landing.heroTitle1')}<br />
            <span className="gradient-text">{t('landing.heroTitle2')}</span>
          </motion.h1>

          {/* Subtitle */}
          <motion.p initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.2 }} 
            style={{ fontSize: 'clamp(18px, 2.5vw, 24px)', color: 'var(--color-text-secondary)', maxWidth: '800px', margin: '0 auto 80px auto', lineHeight: '1.6' }}>
            {t('landing.heroSubtitle')}
          </motion.p>

          {/* Buttons */}
          <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.3 }} 
            style={{ display: 'flex', flexWrap: 'wrap', gap: '20px', justifyContent: 'center', marginBottom: '100px' }}>
            <Link to="/register" className="btn btn-primary" style={{ fontSize: '18px', padding: '20px 40px' }}>
              {t('landing.startFreeTrial')} <ArrowRight style={{ width: '20px', height: '20px' }} />
            </Link>
            <a href="#how-it-works" className="btn btn-secondary" style={{ fontSize: '18px', padding: '20px 40px' }}>
              {t('landing.seeHowItWorks')}
            </a>
          </motion.div>

          {/* Stats */}
          <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.4 }} 
            style={{ width: '100%', maxWidth: '800px', margin: '0 auto' }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '40px' }}>
              {stats.map((stat, i) => (
                <div key={i} style={{ textAlign: 'center' }}>
                  <div className="gradient-text" style={{ fontSize: 'clamp(32px, 4vw, 48px)', fontWeight: '700', marginBottom: '12px' }}>{stat.value}</div>
                  <div style={{ fontSize: '14px', color: 'var(--color-text-muted)' }}>{stat.label}</div>
                </div>
              ))}
            </div>
          </motion.div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" style={{ padding: '160px 24px', scrollMarginTop: '96px' }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: '100px' }}>
            <motion.h2 initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
              style={{ fontSize: 'clamp(36px, 5vw, 56px)', fontWeight: '700', marginBottom: '24px' }}>
              {t('landing.featuresTitle1')} <span className="gradient-text">{t('landing.featuresTitle2')}</span>
            </motion.h2>
            <motion.p initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: 0.1 }}
              style={{ fontSize: '20px', color: 'var(--color-text-secondary)', maxWidth: '700px', margin: '0 auto' }}>
              {t('landing.featuresSubtitle')}
            </motion.p>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '32px' }}>
            {features.map((feature, i) => {
              const Icon = feature.icon
              return (
                <motion.div key={i} initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.1 }}
                  className="feature-card" style={{ padding: '40px' }}>
                  <div className="gradient-bg" style={{ width: '64px', height: '64px', borderRadius: '16px', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '28px' }}>
                    <Icon style={{ width: '32px', height: '32px', color: 'white' }} />
                  </div>
                  <h3 style={{ fontSize: '22px', fontWeight: '700', marginBottom: '16px' }}>{feature.title}</h3>
                  <p style={{ fontSize: '16px', color: 'var(--color-text-muted)', lineHeight: '1.7' }}>{feature.description}</p>
                </motion.div>
              )
            })}
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section id="how-it-works" style={{ padding: '160px 24px', backgroundColor: 'var(--color-bg-secondary)', scrollMarginTop: '96px' }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: '100px' }}>
            <motion.h2 initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
              style={{ fontSize: 'clamp(36px, 5vw, 56px)', fontWeight: '700', marginBottom: '24px' }}>
              {t('landing.howItWorksTitle')} <span className="gradient-text">{t('landing.howItWorksTitle2')}</span>
            </motion.h2>
            <motion.p initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: 0.1 }}
              style={{ fontSize: '20px', color: 'var(--color-text-secondary)' }}>
              {t('landing.howItWorksSubtitle')}
            </motion.p>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '60px' }}>
            {steps.map((step, i) => (
              <motion.div key={i} initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.15 }}
                style={{ textAlign: 'center' }}>
                <div className="gradient-bg" style={{ width: '88px', height: '88px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 32px auto', fontSize: '36px', fontWeight: '700', color: 'white', boxShadow: '0 20px 40px rgba(6, 182, 212, 0.25)' }}>
                  {step.num}
                </div>
                <h3 style={{ fontSize: '22px', fontWeight: '700', marginBottom: '16px' }}>{step.title}</h3>
                <p style={{ fontSize: '16px', color: 'var(--color-text-muted)', lineHeight: '1.7' }}>{step.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonials Section */}
      <section style={{ padding: '160px 24px' }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: '80px' }}>
            <motion.h2 initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
              style={{ fontSize: 'clamp(36px, 5vw, 56px)', fontWeight: '700', marginBottom: '24px' }}>
              {t('landing.trustedBy')} <span className="gradient-text">{t('landing.industryLeaders')}</span>
            </motion.h2>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '32px' }}>
            {testimonials.map((tst, i) => (
              <motion.div key={i} initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.1 }}
                className="card" style={{ padding: '40px' }}>
                <p style={{ fontSize: '18px', color: 'var(--color-text-secondary)', marginBottom: '32px', lineHeight: '1.7' }}>"{tst.quote}"</p>
                <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                  <div className="gradient-bg" style={{ width: '52px', height: '52px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <Users style={{ width: '26px', height: '26px', color: 'white' }} />
                  </div>
                  <div>
                    <div style={{ fontWeight: '600', fontSize: '16px' }}>{tst.author}</div>
                    <div style={{ fontSize: '14px', color: 'var(--color-text-muted)' }}>{tst.role}</div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section style={{ padding: '120px 24px 160px 24px' }}>
        <div style={{ maxWidth: '1000px', margin: '0 auto' }}>
          <motion.div initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
            className="gradient-border" style={{ padding: '80px 40px', textAlign: 'center' }}>
            <h2 style={{ fontSize: 'clamp(32px, 4vw, 48px)', fontWeight: '700', marginBottom: '24px' }}>{t('landing.readyToTest')}</h2>
            <p style={{ fontSize: '20px', color: 'var(--color-text-secondary)', maxWidth: '600px', margin: '0 auto 48px auto', lineHeight: '1.6' }}>
              {t('landing.ctaSubtitle')}
            </p>
            <Link to="/register" className="btn btn-primary" style={{ fontSize: '18px', padding: '20px 40px' }}>
              {t('landing.getStartedFree')} <ArrowRight style={{ width: '20px', height: '20px' }} />
            </Link>
          </motion.div>
        </div>
      </section>

      <Footer />
    </div>
  )
}

export default Landing
