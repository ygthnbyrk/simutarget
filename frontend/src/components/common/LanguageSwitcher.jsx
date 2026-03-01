import { useState, useRef, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { Globe, ChevronDown, Check } from 'lucide-react'

function LanguageSwitcher({ compact = false }) {
  const { i18n } = useTranslation()
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef(null)

  const currentLang = i18n.language?.startsWith('tr') ? 'tr' : 'en'

  const languages = [
    { code: 'en', label: 'EN', fullLabel: 'English' },
    { code: 'tr', label: 'TR', fullLabel: 'Türkçe' },
  ]

  const currentLangData = languages.find(l => l.code === currentLang) || languages[0]

  // Close on outside click
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const selectLanguage = (code) => {
    i18n.changeLanguage(code)
    setIsOpen(false)
  }

  return (
    <div ref={dropdownRef} style={{ position: 'relative', zIndex: 100 }}>
      {/* Trigger Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: compact ? '6px' : '8px',
          padding: compact ? '8px 12px' : '10px 16px',
          borderRadius: '12px',
          background: 'var(--color-bg-tertiary)',
          border: '1px solid var(--color-border)',
          cursor: 'pointer',
          transition: 'all 0.2s',
          color: 'var(--color-text-secondary)',
          fontSize: compact ? '13px' : '14px',
          fontWeight: '600',
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.borderColor = 'var(--color-accent-cyan)'
          e.currentTarget.style.background = 'rgba(6, 182, 212, 0.08)'
        }}
        onMouseLeave={(e) => {
          if (!isOpen) {
            e.currentTarget.style.borderColor = 'var(--color-border)'
            e.currentTarget.style.background = 'var(--color-bg-tertiary)'
          }
        }}
      >
        <Globe style={{ width: compact ? '16px' : '18px', height: compact ? '16px' : '18px', color: 'var(--color-accent-cyan)' }} />
        <span>{currentLangData.label}</span>
        <ChevronDown style={{
          width: '14px',
          height: '14px',
          color: 'var(--color-text-muted)',
          transition: 'transform 0.2s',
          transform: isOpen ? 'rotate(180deg)' : 'rotate(0deg)',
        }} />
      </button>

      {/* Dropdown */}
      {isOpen && (
        <div style={{
          position: 'absolute',
          top: 'calc(100% + 8px)',
          right: 0,
          minWidth: '180px',
          background: 'var(--color-bg-secondary)',
          border: '1px solid var(--color-border)',
          borderRadius: '14px',
          padding: '6px',
          boxShadow: '0 16px 48px rgba(0, 0, 0, 0.4), 0 0 0 1px rgba(6, 182, 212, 0.1)',
          animation: 'fadeInDown 0.15s ease-out',
        }}>
          {languages.map((lang) => {
            const isActive = currentLang === lang.code
            return (
              <button
                key={lang.code}
                onClick={() => selectLanguage(lang.code)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  width: '100%',
                  padding: '12px 16px',
                  borderRadius: '10px',
                  border: 'none',
                  cursor: 'pointer',
                  transition: 'all 0.15s',
                  background: isActive ? 'rgba(6, 182, 212, 0.12)' : 'transparent',
                  color: isActive ? 'var(--color-accent-cyan)' : 'var(--color-text-secondary)',
                  fontSize: '14px',
                  fontWeight: isActive ? '600' : '500',
                }}
                onMouseEnter={(e) => {
                  if (!isActive) {
                    e.currentTarget.style.background = 'rgba(255, 255, 255, 0.05)'
                  }
                }}
                onMouseLeave={(e) => {
                  if (!isActive) {
                    e.currentTarget.style.background = 'transparent'
                  }
                }}
              >
                <span style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span style={{ fontWeight: '700', fontSize: '13px', opacity: 0.7 }}>{lang.label}</span>
                  <span>{lang.fullLabel}</span>
                </span>
                {isActive && (
                  <Check style={{ width: '16px', height: '16px', color: 'var(--color-accent-cyan)' }} />
                )}
              </button>
            )
          })}
        </div>
      )}

      {/* Animation keyframes */}
      <style>{`
        @keyframes fadeInDown {
          from { opacity: 0; transform: translateY(-8px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  )
}

export default LanguageSwitcher