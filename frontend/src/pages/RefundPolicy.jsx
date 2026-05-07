import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import { ShieldCheck } from 'lucide-react'
import LegalPageLayout from '../components/LegalPageLayout'

const sectionStyle = { marginBottom: '40px' }
const headingStyle = { fontSize: '20px', fontWeight: '700', color: 'var(--color-text-primary)', marginBottom: '14px' }
const textStyle = { fontSize: '15px', lineHeight: '1.8', color: 'var(--color-text-secondary)', marginBottom: '12px' }
const linkStyle = { color: 'var(--color-accent-cyan)', textDecoration: 'underline' }

function RefundPolicy() {
  const { t } = useTranslation()

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
          {t('refund.lastUpdated')}: May 2026
        </p>
      </div>

      {/* Lemon Squeezy Notice Badge */}
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
        {/* 1. Overview */}
        <div style={sectionStyle}>
          <h2 style={headingStyle}>1. {t('refund.overview_title')}</h2>
          <p style={textStyle}>{t('refund.overview_text')}</p>
          <p style={textStyle}>{t('refund.overview_text2')}</p>
        </div>

        {/* 2. Lemon Squeezy Refund Policy */}
        <div style={sectionStyle}>
          <h2 style={headingStyle}>2. {t('refund.paddle_title')}</h2>
          <p style={textStyle}>
            {t('refund.paddle_text')}{' '}
            <a
              href="https://www.lemonsqueezy.com/policies/refund-policy"
              target="_blank"
              rel="noopener noreferrer"
              style={linkStyle}
            >
              https://www.lemonsqueezy.com/policies/refund-policy
            </a>
          </p>
          <p style={textStyle}>{t('refund.paddle_text2')}</p>
        </div>

        {/* 3. Statutory Rights */}
        <div style={sectionStyle}>
          <h2 style={headingStyle}>3. {t('refund.statutory_title')}</h2>
          <p style={textStyle}>{t('refund.statutory_text')}</p>
          <ul style={{ ...textStyle, paddingLeft: '24px', listStyle: 'disc' }}>
            <li style={{ marginBottom: '8px' }}>{t('refund.statutory_eu')}</li>
            <li style={{ marginBottom: '8px' }}>{t('refund.statutory_apac')}</li>
            <li style={{ marginBottom: '8px' }}>{t('refund.statutory_singapore')}</li>
            <li style={{ marginBottom: '8px' }}>{t('refund.statutory_discretionary')}</li>
          </ul>
          <p style={textStyle}>{t('refund.statutory_text2')}</p>
        </div>

        {/* 4. How to Request a Refund */}
        <div style={sectionStyle}>
          <h2 style={headingStyle}>4. {t('refund.process_title')}</h2>
          <p style={textStyle}>{t('refund.process_text')}</p>
          <ul style={{ ...textStyle, paddingLeft: '24px', listStyle: 'disc' }}>
            <li style={{ marginBottom: '8px' }}>{t('refund.process_method1')}</li>
            <li style={{ marginBottom: '8px' }}>
              {t('refund.process_method2')}{' '}
              <a
                href="https://app.lemonsqueezy.com/my-orders"
                target="_blank"
                rel="noopener noreferrer"
                style={linkStyle}
              >
                app.lemonsqueezy.com/my-orders
              </a>
            </li>
            <li style={{ marginBottom: '8px' }}>{t('refund.process_method3')}</li>
          </ul>
          <p style={textStyle}>{t('refund.process_text2')}</p>
        </div>

        {/* 5. Cancellations */}
        <div style={sectionStyle}>
          <h2 style={headingStyle}>5. {t('refund.cancel_title')}</h2>
          <p style={textStyle}>{t('refund.cancel_text')}</p>
        </div>

        {/* 6. Contact */}
        <div style={sectionStyle}>
          <h2 style={headingStyle}>6. {t('refund.contact_title')}</h2>
          <p style={textStyle}>
            {t('refund.contact_text')}{' '}
            <a
              href="https://app.lemonsqueezy.com/my-orders"
              target="_blank"
              rel="noopener noreferrer"
              style={linkStyle}
            >
              app.lemonsqueezy.com/my-orders
            </a>
            .
          </p>
          <p style={textStyle}>
            {t('refund.contact_text2')}{' '}
            <a href="mailto:contact@simutarget.ai" style={linkStyle}>
              contact@simutarget.ai
            </a>
          </p>
        </div>
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
