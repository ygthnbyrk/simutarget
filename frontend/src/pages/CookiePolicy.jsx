import { useTranslation } from 'react-i18next'
import LegalPageLayout from '../components/LegalPageLayout'

const sectionStyle = { marginBottom: '40px' }
const headingStyle = { fontSize: '20px', fontWeight: '700', color: 'var(--color-text-primary)', marginBottom: '14px' }
const textStyle = { fontSize: '15px', lineHeight: '1.8', color: 'var(--color-text-secondary)', marginBottom: '12px' }

function CookiePolicy() {
  const { t } = useTranslation()

  const sections = ['intro', 'what', 'types', 'howWeUse', 'thirdParty', 'manage', 'changes', 'contact']

  return (
    <LegalPageLayout>
      <div style={{ textAlign: 'center', marginBottom: '48px' }}>
        <h1 style={{ fontSize: '42px', fontWeight: '800', marginBottom: '16px' }}>
          <span className="gradient-text">{t('cookie.title')}</span>
        </h1>
        <p style={{ fontSize: '15px', color: 'var(--color-text-muted)' }}>
          {t('cookie.lastUpdated')}: February 2025
        </p>
      </div>

      <div style={{
        padding: '40px',
        borderRadius: '20px',
        background: 'rgba(255,255,255,0.02)',
        border: '1px solid rgba(255,255,255,0.06)',
      }}>
        {sections.map((sec, i) => (
          <div key={sec} style={sectionStyle}>
            <h2 style={headingStyle}>{i + 1}. {t(`cookie.${sec}_title`)}</h2>
            <p style={textStyle}>{t(`cookie.${sec}_text`)}</p>
            {t(`cookie.${sec}_text2`, { defaultValue: '' }) && (
              <p style={textStyle}>{t(`cookie.${sec}_text2`)}</p>
            )}
          </div>
        ))}
      </div>
    </LegalPageLayout>
  )
}

export default CookiePolicy
