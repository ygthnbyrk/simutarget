import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { ChevronDown, HelpCircle } from 'lucide-react'
import { Link } from 'react-router-dom'
import LegalPageLayout from '../components/LegalPageLayout'

function FAQItem({ question, answer, isOpen, onClick }) {
  return (
    <div style={{
      borderRadius: '14px',
      background: isOpen ? 'rgba(6,182,212,0.05)' : 'rgba(255,255,255,0.03)',
      border: `1px solid ${isOpen ? 'rgba(6,182,212,0.2)' : 'rgba(255,255,255,0.08)'}`,
      transition: 'all 0.3s',
      overflow: 'hidden',
    }}>
      <button
        onClick={onClick}
        style={{
          width: '100%',
          padding: '20px 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: 'transparent',
          border: 'none',
          cursor: 'pointer',
          color: 'var(--color-text-primary)',
          fontSize: '16px',
          fontWeight: '600',
          textAlign: 'left',
          gap: '16px',
        }}
      >
        <span>{question}</span>
        <ChevronDown style={{
          width: '20px', height: '20px', flexShrink: 0,
          color: 'var(--color-accent-cyan)',
          transform: isOpen ? 'rotate(180deg)' : 'rotate(0)',
          transition: 'transform 0.3s',
        }} />
      </button>
      <div style={{
        maxHeight: isOpen ? '500px' : '0',
        overflow: 'hidden',
        transition: 'max-height 0.4s ease',
      }}>
        <div style={{ padding: '0 24px 20px 24px', color: 'var(--color-text-secondary)', fontSize: '15px', lineHeight: '1.8' }}>
          {answer}
        </div>
      </div>
    </div>
  )
}

function FAQs() {
  const { t } = useTranslation()
  const [openIndex, setOpenIndex] = useState(0)

  const categories = ['general', 'pricing', 'technical', 'account']

  const faqsByCategory = {}
  categories.forEach(cat => {
    faqsByCategory[cat] = []
    for (let i = 1; i <= 4; i++) {
      const q = t(`faq.${cat}_q${i}`, { defaultValue: '' })
      const a = t(`faq.${cat}_a${i}`, { defaultValue: '' })
      if (q) faqsByCategory[cat].push({ q, a })
    }
  })

  let globalIdx = 0

  return (
    <LegalPageLayout>
      {/* Page Title */}
      <div style={{ textAlign: 'center', marginBottom: '64px' }}>
        <div style={{ width: '64px', height: '64px', borderRadius: '50%', background: 'rgba(6,182,212,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 20px' }}>
          <HelpCircle style={{ width: '32px', height: '32px', color: 'var(--color-accent-cyan)' }} />
        </div>
        <h1 style={{ fontSize: '42px', fontWeight: '800', marginBottom: '16px' }}>
          <span className="gradient-text">{t('faq.title')}</span>
        </h1>
        <p style={{ fontSize: '18px', color: 'var(--color-text-secondary)', maxWidth: '600px', margin: '0 auto' }}>
          {t('faq.subtitle')}
        </p>
      </div>

      {/* FAQ Categories */}
      {categories.map(cat => {
        const items = faqsByCategory[cat]
        if (!items.length) return null
        return (
          <div key={cat} style={{ marginBottom: '48px' }}>
            <h2 style={{ fontSize: '20px', fontWeight: '700', color: 'var(--color-text-primary)', marginBottom: '20px', textTransform: 'capitalize' }}>
              {t(`faq.category_${cat}`)}
            </h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {items.map((item, i) => {
                const idx = globalIdx++
                return (
                  <FAQItem
                    key={idx}
                    question={item.q}
                    answer={item.a}
                    isOpen={openIndex === idx}
                    onClick={() => setOpenIndex(openIndex === idx ? -1 : idx)}
                  />
                )
              })}
            </div>
          </div>
        )
      })}

      {/* Still have questions? */}
      <div style={{
        textAlign: 'center',
        padding: '48px',
        borderRadius: '20px',
        background: 'rgba(255,255,255,0.03)',
        border: '1px solid rgba(255,255,255,0.08)',
      }}>
        <h3 style={{ fontSize: '20px', fontWeight: '700', color: 'var(--color-text-primary)', marginBottom: '12px' }}>
          {t('faq.stillHaveQuestions')}
        </h3>
        <p style={{ color: 'var(--color-text-secondary)', marginBottom: '20px' }}>
          {t('faq.stillHaveQuestionsDesc')}
        </p>
        <Link to="/contact" className="btn btn-primary" style={{ display: 'inline-flex', padding: '12px 28px' }}>
          {t('faq.contactUs')}
        </Link>
      </div>
    </LegalPageLayout>
  )
}

export default FAQs
