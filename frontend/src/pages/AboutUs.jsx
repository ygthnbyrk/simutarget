import { useTranslation } from 'react-i18next'
import { Target, Zap, Globe, Shield, Users, TrendingUp } from 'lucide-react'
import LegalPageLayout from '../components/LegalPageLayout'

const sectionStyle = {
  marginBottom: '48px',
}

const headingStyle = {
  fontSize: '22px',
  fontWeight: '700',
  color: 'var(--color-text-primary)',
  marginBottom: '16px',
}

const textStyle = {
  fontSize: '16px',
  lineHeight: '1.8',
  color: 'var(--color-text-secondary)',
  marginBottom: '16px',
}

function AboutUs() {
  const { t } = useTranslation()

  const values = [
    { icon: Target, key: 'accuracy' },
    { icon: Shield, key: 'privacy' },
    { icon: Globe, key: 'global' },
    { icon: Zap, key: 'speed' },
    { icon: Users, key: 'accessibility' },
    { icon: TrendingUp, key: 'innovation' },
  ]

  return (
    <LegalPageLayout>
      {/* Page Title */}
      <div style={{ textAlign: 'center', marginBottom: '64px' }}>
        <h1 style={{ fontSize: '42px', fontWeight: '800', marginBottom: '16px' }}>
          <span className="gradient-text">{t('about.title')}</span>
        </h1>
        <p style={{ fontSize: '18px', color: 'var(--color-text-secondary)', maxWidth: '600px', margin: '0 auto' }}>
          {t('about.subtitle')}
        </p>
      </div>

      {/* Mission */}
      <div style={sectionStyle}>
        <h2 style={headingStyle}>{t('about.missionTitle')}</h2>
        <p style={textStyle}>{t('about.missionText1')}</p>
        <p style={textStyle}>{t('about.missionText2')}</p>
      </div>

      {/* What We Do */}
      <div style={sectionStyle}>
        <h2 style={headingStyle}>{t('about.whatWeDoTitle')}</h2>
        <p style={textStyle}>{t('about.whatWeDoText1')}</p>
        <p style={textStyle}>{t('about.whatWeDoText2')}</p>
      </div>

      {/* Our Values */}
      <div style={sectionStyle}>
        <h2 style={headingStyle}>{t('about.valuesTitle')}</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: '20px', marginTop: '24px' }}>
          {values.map(({ icon: Icon, key }) => (
            <div key={key} style={{
              padding: '24px',
              borderRadius: '16px',
              background: 'rgba(255,255,255,0.03)',
              border: '1px solid rgba(255,255,255,0.08)',
              transition: 'all 0.3s',
            }}
              onMouseEnter={(e) => { e.currentTarget.style.borderColor = 'rgba(6,182,212,0.3)'; e.currentTarget.style.transform = 'translateY(-2px)' }}
              onMouseLeave={(e) => { e.currentTarget.style.borderColor = 'rgba(255,255,255,0.08)'; e.currentTarget.style.transform = 'translateY(0)' }}
            >
              <Icon style={{ width: '28px', height: '28px', color: 'var(--color-accent-cyan)', marginBottom: '12px' }} />
              <h3 style={{ fontSize: '16px', fontWeight: '600', color: 'var(--color-text-primary)', marginBottom: '8px' }}>
                {t(`about.value_${key}`)}
              </h3>
              <p style={{ fontSize: '14px', color: 'var(--color-text-muted)', lineHeight: '1.6' }}>
                {t(`about.value_${key}_desc`)}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Company Info */}
      <div style={sectionStyle}>
        <h2 style={headingStyle}>{t('about.companyTitle')}</h2>
        <p style={textStyle}>{t('about.companyText')}</p>
      </div>
    </LegalPageLayout>
  )
}

export default AboutUs