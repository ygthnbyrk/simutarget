import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Mail, MapPin, Clock, Send, MessageSquare, Headphones, Building } from 'lucide-react'
import LegalPageLayout from '../components/LegalPageLayout'

function Contact() {
  const { t } = useTranslation()
  const [form, setForm] = useState({ name: '', email: '', subject: '', message: '' })
  const [sending, setSending] = useState(false)
  const [sent, setSent] = useState(false)

  const handleSubmit = (e) => {
    e.preventDefault()
    setSending(true)
    // Simulate send
    setTimeout(() => {
      setSending(false)
      setSent(true)
      setForm({ name: '', email: '', subject: '', message: '' })
    }, 1500)
  }

  const contactInfo = [
    { icon: Mail, label: t('contact.emailLabel'), value: 'contact@simutarget.ai' },
    { icon: MapPin, label: t('contact.locationLabel'), value: 'Delaware, USA' },
    { icon: Clock, label: t('contact.hoursLabel'), value: t('contact.hoursValue') },
  ]

  const topics = [
    { icon: MessageSquare, key: 'general' },
    { icon: Headphones, key: 'support' },
    { icon: Building, key: 'partnership' },
  ]

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

  return (
    <LegalPageLayout>
      {/* Page Title */}
      <div style={{ textAlign: 'center', marginBottom: '64px' }}>
        <h1 style={{ fontSize: '42px', fontWeight: '800', marginBottom: '16px' }}>
          <span className="gradient-text">{t('contact.title')}</span>
        </h1>
        <p style={{ fontSize: '18px', color: 'var(--color-text-secondary)', maxWidth: '600px', margin: '0 auto' }}>
          {t('contact.subtitle')}
        </p>
      </div>

      {/* Contact Info Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '16px', marginBottom: '48px' }}>
        {contactInfo.map(({ icon: Icon, label, value }) => (
          <div key={label} style={{
            padding: '24px',
            borderRadius: '16px',
            background: 'rgba(255,255,255,0.03)',
            border: '1px solid rgba(255,255,255,0.08)',
            textAlign: 'center',
          }}>
            <Icon style={{ width: '28px', height: '28px', color: 'var(--color-accent-cyan)', marginBottom: '12px' }} />
            <p style={{ fontSize: '13px', color: 'var(--color-text-muted)', marginBottom: '4px' }}>{label}</p>
            <p style={{ fontSize: '15px', fontWeight: '600', color: 'var(--color-text-primary)' }}>{value}</p>
          </div>
        ))}
      </div>

      {/* Topics */}
      <div style={{ marginBottom: '48px' }}>
        <h2 style={{ fontSize: '22px', fontWeight: '700', color: 'var(--color-text-primary)', marginBottom: '20px' }}>
          {t('contact.topicsTitle')}
        </h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '16px' }}>
          {topics.map(({ icon: Icon, key }) => (
            <div key={key} style={{
              padding: '20px',
              borderRadius: '12px',
              background: 'rgba(255,255,255,0.03)',
              border: '1px solid rgba(255,255,255,0.08)',
            }}>
              <Icon style={{ width: '24px', height: '24px', color: 'var(--color-accent-purple)', marginBottom: '10px' }} />
              <h3 style={{ fontSize: '15px', fontWeight: '600', color: 'var(--color-text-primary)', marginBottom: '6px' }}>
                {t(`contact.topic_${key}`)}
              </h3>
              <p style={{ fontSize: '13px', color: 'var(--color-text-muted)', lineHeight: '1.5' }}>
                {t(`contact.topic_${key}_desc`)}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Contact Form */}
      <div style={{
        padding: '40px',
        borderRadius: '20px',
        background: 'rgba(255,255,255,0.03)',
        border: '1px solid rgba(255,255,255,0.08)',
      }}>
        <h2 style={{ fontSize: '22px', fontWeight: '700', color: 'var(--color-text-primary)', marginBottom: '24px' }}>
          {t('contact.formTitle')}
        </h2>

        {sent ? (
          <div style={{ textAlign: 'center', padding: '40px 0' }}>
            <div style={{ width: '64px', height: '64px', borderRadius: '50%', background: 'rgba(6,182,212,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px' }}>
              <Send style={{ width: '28px', height: '28px', color: 'var(--color-accent-cyan)' }} />
            </div>
            <h3 style={{ fontSize: '20px', fontWeight: '700', color: 'var(--color-text-primary)', marginBottom: '8px' }}>{t('contact.sentTitle')}</h3>
            <p style={{ color: 'var(--color-text-secondary)' }}>{t('contact.sentDesc')}</p>
            <button onClick={() => setSent(false)} style={{
              marginTop: '20px', padding: '10px 24px', borderRadius: '10px',
              background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)',
              color: 'var(--color-text-primary)', cursor: 'pointer', fontSize: '14px',
            }}>{t('contact.sendAnother')}</button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: '600', color: 'var(--color-text-muted)', marginBottom: '8px' }}>{t('contact.nameLabel')}</label>
                <input
                  style={inputStyle}
                  placeholder={t('contact.namePlaceholder')}
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  required
                  onFocus={(e) => e.target.style.borderColor = 'var(--color-accent-cyan)'}
                  onBlur={(e) => e.target.style.borderColor = 'rgba(255,255,255,0.1)'}
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: '600', color: 'var(--color-text-muted)', marginBottom: '8px' }}>{t('contact.emailFieldLabel')}</label>
                <input
                  type="email"
                  style={inputStyle}
                  placeholder={t('contact.emailPlaceholder')}
                  value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                  required
                  onFocus={(e) => e.target.style.borderColor = 'var(--color-accent-cyan)'}
                  onBlur={(e) => e.target.style.borderColor = 'rgba(255,255,255,0.1)'}
                />
              </div>
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '13px', fontWeight: '600', color: 'var(--color-text-muted)', marginBottom: '8px' }}>{t('contact.subjectLabel')}</label>
              <input
                style={inputStyle}
                placeholder={t('contact.subjectPlaceholder')}
                value={form.subject}
                onChange={(e) => setForm({ ...form, subject: e.target.value })}
                required
                onFocus={(e) => e.target.style.borderColor = 'var(--color-accent-cyan)'}
                onBlur={(e) => e.target.style.borderColor = 'rgba(255,255,255,0.1)'}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '13px', fontWeight: '600', color: 'var(--color-text-muted)', marginBottom: '8px' }}>{t('contact.messageLabel')}</label>
              <textarea
                style={{ ...inputStyle, minHeight: '140px', resize: 'vertical' }}
                placeholder={t('contact.messagePlaceholder')}
                value={form.message}
                onChange={(e) => setForm({ ...form, message: e.target.value })}
                required
                onFocus={(e) => e.target.style.borderColor = 'var(--color-accent-cyan)'}
                onBlur={(e) => e.target.style.borderColor = 'rgba(255,255,255,0.1)'}
              />
            </div>
            <button type="submit" disabled={sending} className="btn btn-primary" style={{ alignSelf: 'flex-start', padding: '14px 32px', fontSize: '15px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Send style={{ width: '16px', height: '16px' }} />
              {sending ? t('contact.sending') : t('contact.sendButton')}
            </button>
          </form>
        )}
      </div>
    </LegalPageLayout>
  )
}

export default Contact