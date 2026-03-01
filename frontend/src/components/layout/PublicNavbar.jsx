import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Menu, X } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import LanguageSwitcher from '../common/LanguageSwitcher'
import logoNavbar from '../../assets/simutarget-logo-navbar.png'

function PublicNavbar() {
  const [isMenuOpen, setIsMenuOpen] = useState(false)
  const { t } = useTranslation()

  const navLinks = [
    { name: t('nav.features'), href: '/#features' },
    { name: t('nav.howItWorks'), href: '/#how-it-works' },
    { name: t('nav.pricing'), href: '/pricing' },
  ]

  return (
    <nav style={{ position: 'fixed', top: 0, left: 0, right: 0, zIndex: 50, background: 'rgba(10, 14, 26, 0.95)', backdropFilter: 'blur(20px)', borderBottom: '1px solid var(--color-border)' }}>
      <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '0 24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', height: '80px' }}>
          {/* Logo */}
          <Link to="/" style={{ display: 'flex', alignItems: 'center', textDecoration: 'none' }}>
            <img src={logoNavbar} alt="SimuTarget.ai" style={{ height: '44px', width: 'auto' }} />
          </Link>

          {/* Desktop Nav */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '40px' }} className="hidden-mobile">
            {navLinks.map((link) => (
              <a key={link.name} href={link.href} style={{ fontSize: '16px', fontWeight: '500', color: 'var(--color-text-secondary)', textDecoration: 'none', transition: 'color 0.2s' }}>
                {link.name}
              </a>
            ))}
          </div>

          {/* Auth Buttons + Language */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }} className="hidden-mobile">
            <LanguageSwitcher />
            <Link to="/login" className="btn btn-ghost" style={{ padding: '12px 20px' }}>{t('nav.login')}</Link>
            <Link to="/register" className="btn btn-primary" style={{ padding: '12px 24px' }}>{t('nav.getStarted')}</Link>
          </div>

          {/* Mobile Menu Button */}
          <button onClick={() => setIsMenuOpen(!isMenuOpen)} style={{ display: 'none', padding: '8px', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--color-text-secondary)' }} className="show-mobile">
            {isMenuOpen ? <X style={{ width: '28px', height: '28px' }} /> : <Menu style={{ width: '28px', height: '28px' }} />}
          </button>
        </div>

        {/* Mobile Menu */}
        {isMenuOpen && (
          <div style={{ padding: '24px 0', borderTop: '1px solid var(--color-border)' }}>
            {navLinks.map((link) => (
              <a key={link.name} href={link.href} onClick={() => setIsMenuOpen(false)} style={{ display: 'block', padding: '12px 0', fontSize: '18px', color: 'var(--color-text-secondary)', textDecoration: 'none' }}>
                {link.name}
              </a>
            ))}
            <div style={{ padding: '16px 0' }}>
              <LanguageSwitcher />
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '8px', paddingTop: '24px', borderTop: '1px solid var(--color-border)' }}>
              <Link to="/login" onClick={() => setIsMenuOpen(false)} className="btn btn-secondary" style={{ width: '100%', padding: '14px' }}>{t('nav.login')}</Link>
              <Link to="/register" onClick={() => setIsMenuOpen(false)} className="btn btn-primary" style={{ width: '100%', padding: '14px' }}>{t('nav.getStarted')}</Link>
            </div>
          </div>
        )}
      </div>
    </nav>
  )
}

export default PublicNavbar
