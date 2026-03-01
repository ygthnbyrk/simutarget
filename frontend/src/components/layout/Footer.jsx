import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Twitter, Linkedin, Github, Mail } from 'lucide-react'
import logoNavbar from '../../assets/simutarget-logo-navbar.png'

function FooterLink({ to, children }) {
  return (
    <Link to={to} style={{ color: 'var(--color-text-muted)', fontSize: '15px', textDecoration: 'none', transition: 'all 0.2s', display: 'inline-block' }}
      onMouseEnter={(e) => { e.currentTarget.style.color = 'var(--color-accent-cyan)'; e.currentTarget.style.transform = 'translateX(4px)' }}
      onMouseLeave={(e) => { e.currentTarget.style.color = 'var(--color-text-muted)'; e.currentTarget.style.transform = 'translateX(0)' }}>
      {children}
    </Link>
  )
}

function Footer() {
  const currentYear = new Date().getFullYear()
  const { t } = useTranslation()

  return (
    <footer style={{ position: 'relative', overflow: 'hidden' }}>
      {/* Gradient Background */}
      <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(135deg, rgba(6, 182, 212, 0.08) 0%, rgba(139, 92, 246, 0.08) 50%, rgba(6, 182, 212, 0.05) 100%)', zIndex: 0 }} />

      {/* Grid Pattern */}
      <div style={{ position: 'absolute', inset: 0, backgroundImage: 'linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.02) 1px, transparent 1px)', backgroundSize: '50px 50px', zIndex: 1 }} />

      {/* Glow Effects - hidden on mobile for performance */}
      <div className="hide-mobile" style={{ position: 'absolute', top: '-100px', left: '20%', width: '400px', height: '400px', background: 'radial-gradient(circle, rgba(6, 182, 212, 0.15) 0%, transparent 70%)', borderRadius: '50%', filter: 'blur(60px)', zIndex: 0 }} />
      <div className="hide-mobile" style={{ position: 'absolute', bottom: '-150px', right: '10%', width: '500px', height: '500px', background: 'radial-gradient(circle, rgba(139, 92, 246, 0.12) 0%, transparent 70%)', borderRadius: '50%', filter: 'blur(80px)', zIndex: 0 }} />

      {/* Top Border */}
      <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: '2px', background: 'linear-gradient(90deg, transparent, var(--color-accent-cyan), var(--color-accent-purple), transparent)', zIndex: 2 }} />

      {/* Content */}
      <div style={{ position: 'relative', zIndex: 10, maxWidth: '1200px', margin: '0 auto', padding: '80px 20px 48px 20px' }}>
        <div className="grid-footer" style={{ display: 'grid', gridTemplateColumns: '1.5fr 1fr 1fr 1fr', gap: '48px', marginBottom: '64px' }}>

          {/* Brand Column */}
          <div>
            <Link to="/" style={{ display: 'inline-block', textDecoration: 'none', marginBottom: '20px' }}>
              <img src={logoNavbar} alt="SimuTarget.ai" style={{ height: '40px', width: 'auto' }} />
            </Link>
            <p style={{ color: 'var(--color-text-secondary)', fontSize: '14px', lineHeight: '1.8', marginBottom: '24px', maxWidth: '280px' }}>
              {t('footer.description')}
            </p>
            <div style={{ display: 'flex', gap: '10px' }}>
              {[
                { Icon: Twitter, href: '#', color: '#1DA1F2' },
                { Icon: Linkedin, href: '#', color: '#0A66C2' },
                { Icon: Github, href: '#', color: '#fff' }
              ].map(({ Icon, href, color }, i) => (
                <a key={i} href={href}
                  style={{ width: '40px', height: '40px', borderRadius: '10px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--color-text-muted)', transition: 'all 0.3s', textDecoration: 'none' }}
                  onMouseEnter={(e) => { e.currentTarget.style.background = `${color}20`; e.currentTarget.style.borderColor = color; e.currentTarget.style.color = color }}
                  onMouseLeave={(e) => { e.currentTarget.style.background = 'rgba(255,255,255,0.05)'; e.currentTarget.style.borderColor = 'rgba(255,255,255,0.1)'; e.currentTarget.style.color = 'var(--color-text-muted)' }}>
                  <Icon style={{ width: '18px', height: '18px' }} />
                </a>
              ))}
            </div>
          </div>

          {/* Product */}
          <div>
            <h4 style={{ fontWeight: '700', fontSize: '15px', marginBottom: '20px', color: 'var(--color-text-primary)' }}>{t('footer.product')}</h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <FooterLink to="/#features">{t('footer.features')}</FooterLink>
              <FooterLink to="/pricing">{t('nav.pricing')}</FooterLink>
              <FooterLink to="/faqs">{t('footer.faqs')}</FooterLink>
              <FooterLink to="/#how-it-works">{t('footer.howItWorks')}</FooterLink>
            </div>
          </div>

          {/* Company */}
          <div>
            <h4 style={{ fontWeight: '700', fontSize: '15px', marginBottom: '20px', color: 'var(--color-text-primary)' }}>{t('footer.company')}</h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <FooterLink to="/about">{t('footer.about')}</FooterLink>
              <FooterLink to="/contact">{t('footer.contact')}</FooterLink>
              <FooterLink to="/partner">{t('footer.partner')}</FooterLink>
            </div>
          </div>

          {/* Legal */}
          <div>
            <h4 style={{ fontWeight: '700', fontSize: '15px', marginBottom: '20px', color: 'var(--color-text-primary)' }}>{t('footer.legal')}</h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <FooterLink to="/terms">{t('footer.termsConditions')}</FooterLink>
              <FooterLink to="/privacy">{t('footer.privacyPolicy')}</FooterLink>
              <FooterLink to="/cookies">{t('footer.cookiePolicy')}</FooterLink>
              <FooterLink to="/refund">{t('footer.refundPolicy')}</FooterLink>
            </div>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="footer-bottom" style={{ paddingTop: '28px', borderTop: '1px solid rgba(255,255,255,0.08)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
          <p style={{ color: 'var(--color-text-muted)', fontSize: '13px' }}>
            © {currentYear} SimuTarget.ai. {t('footer.allRightsReserved')}
          </p>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--color-text-muted)', fontSize: '13px' }}>
            <Mail style={{ width: '15px', height: '15px' }} />
            <span>contact@simutarget.ai</span>
          </div>
        </div>
      </div>
    </footer>
  )
}

export default Footer
