import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Handshake, TrendingUp, Users, Globe, DollarSign, Send, CheckCircle } from 'lucide-react'
import LegalPageLayout from '../components/LegalPageLayout'

const inputStyle = {
  width: '100%',
  padding: '14px 16px',
  borderRadius: '12px',
  border: '1px solid rgba(255,255,255,0.1)',
  background: 'rgba(255,255,255,0.05)',
  color: 'var(--color-text-primary)',
  fontSize: '15px',
  outline: 'none',
  transition: 'border-color 0.2s',
}

function Partner() {
  const { t } = useTranslation()
  const [form, setForm] = useState({ name: '', email: '', company: '', type: '', message: '' })
  const [sending, setSending] = useState(false)
  const [sent, setSent] = useState(false)

  const handleSubmit = (e) => {
    e.preventDefault()
    setSending(true)
    setTimeout(() => { setSending(false); setSent(true) }, 1500)
  }

  const benefits = [
    { icon: DollarSign, key: 'revenue' },
    { icon: Users, key: 'network' },
    { icon: TrendingUp, key: 'growth' },
    { icon: Globe, key: 'global' },
  ]

  const partnerTypes = ['agency', 'reseller', 'technology', 'affiliate']

  return (
    <LegalPageLayout>
      {/* Page Title */}
      <div style={{ textAlign: 'center', marginBottom: '64px' }}>
        <div style={{ width: '64px', height: '64px', borderRadius: '50%', background: 'rgba(139,92,246,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 20px' }}>
          <Handshake style={{ width: '32px', height: '32px', color: 'var(--color-accent-purple)' }} />
        </div>
        <h1 style={{ fontSize: '42px', fontWeight: '800', marginBottom: '16px' }}>
          <span className="gradient-text">{t('partner.title')}</span>
        </h1>
        <p style={{ fontSize: '18px', color: 'var(--color-text-secondary)', maxWidth: '600px', margin: '0 auto' }}>
          {t('partner.subtitle')}
        </p>
      </div>

      {/* Benefits */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '16px', marginBottom: '48px' }}>
        {benefits.map(({ icon: Icon, key }) => (
          <div key={key} style={{
            padding: '24px',
            borderRadius: '16px',
            background: 'rgba(255,255,255,0.03)',
            border: '1px solid rgba(255,255,255,0.08)',
            textAlign: 'center',
          }}>
            <Icon style={{ width: '28px', height: '28px', color: 'var(--color-accent-cyan)', marginBottom: '12px' }} />
            <h3 style={{ fontSize: '15px', fontWeight: '600', color: 'var(--color-text-primary)', marginBottom: '6px' }}>
              {t(`partner.benefit_${key}`)}
            </h3>
            <p style={{ fontSize: '13px', color: 'var(--color-text-muted)', lineHeight: '1.5' }}>
              {t(`partner.benefit_${key}_desc`)}
            </p>
          </div>
        ))}
      </div>

      {/* Partner Types */}
      <div style={{ marginBottom: '48px' }}>
        <h2 style={{ fontSize: '22px', fontWeight: '700', color: 'var(--color-text-primary)', marginBottom: '20px' }}>
          {t('partner.typesTitle')}
        </h2>
        <div className="grid-2-responsive" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
          {partnerTypes.map(type => (
            <div key={type} style={{
              padding: '20px',
              borderRadius: '14px',
              background: 'rgba(255,255,255,0.03)',
              border: '1px solid rgba(255,255,255,0.08)',
            }}>
              <h3 style={{ fontSize: '16px', fontWeight: '600', color: 'var(--color-text-primary)', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <CheckCircle style={{ width: '18px', height: '18px', color: 'var(--color-accent-cyan)' }} />
                {t(`partner.type_${type}`)}
              </h3>
              <p style={{ fontSize: '14px', color: 'var(--color-text-muted)', lineHeight: '1.6' }}>
                {t(`partner.type_${type}_desc`)}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Application Form */}
      <div style={{
        padding: '40px',
        borderRadius: '20px',
        background: 'rgba(255,255,255,0.03)',
        border: '1px solid rgba(255,255,255,0.08)',
      }}>
        <h2 style={{ fontSize: '22px', fontWeight: '700', color: 'var(--color-text-primary)', marginBottom: '24px' }}>
          {t('partner.formTitle')}
        </h2>

        {sent ? (
          <div style={{ textAlign: 'center', padding: '40px 0' }}>
            <div style={{ width: '64px', height: '64px', borderRadius: '50%', background: 'rgba(6,182,212,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px' }}>
              <Handshake style={{ width: '28px', height: '28px', color: 'var(--color-accent-cyan)' }} />
            </div>
            <h3 style={{ fontSize: '20px', fontWeight: '700', color: 'var(--color-text-primary)', marginBottom: '8px' }}>{t('partner.sentTitle')}</h3>
            <p style={{ color: 'var(--color-text-secondary)' }}>{t('partner.sentDesc')}</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <div className="grid-2-responsive" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: '600', color: 'var(--color-text-muted)', marginBottom: '8px' }}>{t('partner.nameLabel')}</label>
                <input style={inputStyle} placeholder={t('partner.namePlaceholder')} value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required
                  onFocus={(e) => e.target.style.borderColor = 'var(--color-accent-cyan)'} onBlur={(e) => e.target.style.borderColor = 'rgba(255,255,255,0.1)'} />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: '600', color: 'var(--color-text-muted)', marginBottom: '8px' }}>{t('partner.emailLabel')}</label>
                <input type="email" style={inputStyle} placeholder={t('partner.emailPlaceholder')} value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required
                  onFocus={(e) => e.target.style.borderColor = 'var(--color-accent-cyan)'} onBlur={(e) => e.target.style.borderColor = 'rgba(255,255,255,0.1)'} />
              </div>
            </div>
            <div className="grid-2-responsive" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: '600', color: 'var(--color-text-muted)', marginBottom: '8px' }}>{t('partner.companyLabel')}</label>
                <input style={inputStyle} placeholder={t('partner.companyPlaceholder')} value={form.company} onChange={(e) => setForm({ ...form, company: e.target.value })} required
                  onFocus={(e) => e.target.style.borderColor = 'var(--color-accent-cyan)'} onBlur={(e) => e.target.style.borderColor = 'rgba(255,255,255,0.1)'} />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: '600', color: 'var(--color-text-muted)', marginBottom: '8px' }}>{t('partner.typeLabel')}</label>
                <select style={{ ...inputStyle, cursor: 'pointer' }} value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value })} required
                  onFocus={(e) => e.target.style.borderColor = 'var(--color-accent-cyan)'} onBlur={(e) => e.target.style.borderColor = 'rgba(255,255,255,0.1)'}>
                  <option value="" style={{ background: '#1a1a2e', color: '#e0e0e0' }}>{t('partner.selectType')}</option>
                  {partnerTypes.map(type => (
                    <option key={type} value={type} style={{ background: '#1a1a2e', color: '#e0e0e0' }}>{t(`partner.type_${type}`)}</option>
                  ))}
                </select>
              </div>
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '13px', fontWeight: '600', color: 'var(--color-text-muted)', marginBottom: '8px' }}>{t('partner.messageLabel')}</label>
              <textarea style={{ ...inputStyle, minHeight: '120px', resize: 'vertical' }} placeholder={t('partner.messagePlaceholder')} value={form.message} onChange={(e) => setForm({ ...form, message: e.target.value })}
                onFocus={(e) => e.target.style.borderColor = 'var(--color-accent-cyan)'} onBlur={(e) => e.target.style.borderColor = 'rgba(255,255,255,0.1)'} />
            </div>
            <button type="submit" disabled={sending} className="btn btn-primary" style={{ alignSelf: 'flex-start', padding: '14px 32px', fontSize: '15px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Send style={{ width: '16px', height: '16px' }} />
              {sending ? t('partner.sending') : t('partner.submitButton')}
            </button>
          </form>
        )}
      </div>
    </LegalPageLayout>
  )
}

export default Partner