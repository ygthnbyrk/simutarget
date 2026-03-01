import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import { ShieldCheck } from 'lucide-react'
import LegalPageLayout from '../components/LegalPageLayout'

const sectionStyle = { marginBottom: '40px' }
const headingStyle = { fontSize: '20px', fontWeight: '700', color: 'var(--color-text-primary)', marginBottom: '14px' }
const textStyle = { fontSize: '15px', lineHeight: '1.8', color: 'var(--color-text-secondary)', marginBottom: '12px' }

function RefundPolicy() {
  const { t } = useTranslation()

  const sections = ['overview', 'eligible', 'notEligible', 'process', 'timeline', 'contact']

  return (
    <LegalPageLayout>
      <div style={{ textAlign: 'center', marginBottom: '48px' }}>
        <div style={{ width: '64px', height: '64px', borderRadius: '50%', background: 'rgba(6,182,212,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 20px' }}>
          <ShieldCheck style={{ width: '32px', height: '32px', color: 'var(--color-accent-cyan)' }} />
        </div>
        <h1 style={{ fontSize: '42px', fontWeight: '800', marginBottom: '16px' }}>
          <span className="gradient-text">{t('refund.title')}</span>
        </h1>
        <p style={{ fontSize: '15px', color: 'var(--color-text-muted)' }}>
          {t('refund.lastUpdated')}: February 2025
        </p>
      </div>

      {/* 30-Day Badge */}
      <div style={{
        padding: '24px 32px',
        borderRadius: '16px',
        background: 'linear-gradient(135deg, rgba(6,182,212,0.1), rgba(139,92,246,0.1))',
        border: '1px solid rgba(6,182,212,0.2)',
        textAlign: 'center',
        marginBottom: '48px',
      }}>
        <p style={{ fontSize: '20px', fontWeight: '700', color: 'var(--color-text-primary)', marginBottom: '4px' }}>
          {t('refund.guaranteeBadge')}
        </p>
        <p style={{ fontSize: '14px', color: 'var(--color-text-secondary)' }}>{t('refund.guaranteeDesc')}</p>
      </div>

      <div style={{
        padding: '40px',
        borderRadius: '20px',
        background: 'rgba(255,255,255,0.02)',
        border: '1px solid rgba(255,255,255,0.06)',
      }}>
        {sections.map((sec, i) => (
          <div key={sec} style={sectionStyle}>
            <h2 style={headingStyle}>{i + 1}. {t(`refund.${sec}_title`)}</h2>
            <p style={textStyle}>{t(`refund.${sec}_text`)}</p>
            {t(`refund.${sec}_text2`, { defaultValue: '' }) && (
              <p style={textStyle}>{t(`refund.${sec}_text2`)}</p>
            )}
          </div>
        ))}
      </div>

      {/* CTA */}
      <div style={{ textAlign: 'center', marginTop: '48px' }}>
        <p style={{ color: 'var(--color-text-secondary)', marginBottom: '16px' }}>{t('refund.needHelp')}</p>
        <Link to="/contact" className="btn btn-primary" style={{ display: 'inline-flex', padding: '12px 28px' }}>
          {t('refund.contactSupport')}
        </Link>
      </div>
    </LegalPageLayout>
  )
}

export default RefundPolicy
