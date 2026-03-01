import { useState, useEffect } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Home, TestTube, Swords, LayoutGrid, History, User, LogOut, CreditCard, Menu, X, ChevronLeft } from 'lucide-react'
import useAuthStore from '../../stores/authStore'
import useCreditStore from '../../stores/creditStore'
import LanguageSwitcher from '../common/LanguageSwitcher'
import logoNavbar from '../../assets/simutarget-logo-navbar.png'


function DashboardLayout({ children }) {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const location = useLocation()
  const navigate = useNavigate()
  const { t } = useTranslation()
  
  const { user, logout, fetchProfile } = useAuthStore()
  const { balance, subscription, fetchBalance, fetchSubscription } = useCreditStore()

  useEffect(() => { fetchProfile(); fetchBalance(); fetchSubscription() }, [])

  const handleLogout = () => { logout(); navigate('/login') }

  const navItems = [
    { name: t('nav.dashboard'), href: '/dashboard', icon: Home },
    { name: t('nav.campaignTest'), href: '/dashboard/test', icon: TestTube },
    { name: t('nav.abCompare'), href: '/dashboard/ab', icon: Swords },
    { name: t('nav.multiCompare'), href: '/dashboard/multi', icon: LayoutGrid, badge: 'Business+' },
    { name: t('nav.history'), href: '/dashboard/history', icon: History },
  ]

  const isActive = (href) => location.pathname === href
  const creditsPercentage = subscription ? Math.min(100, Math.round((balance / subscription.credits_monthly) * 100)) : 0

  return (
    <div style={{ minHeight: '100vh', background: 'var(--color-bg-primary)', display: 'flex' }}>
      {/* Mobile Header */}
      <div style={{ position: 'fixed', top: 0, left: 0, right: 0, zIndex: 50, background: 'var(--color-bg-secondary)', borderBottom: '1px solid var(--color-border)', padding: '0 16px', height: '64px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }} className="show-mobile-only">
        <Link to="/dashboard" style={{ display: 'flex', alignItems: 'center', textDecoration: 'none' }}>
          <img src={logoNavbar} alt="SimuTarget" style={{ height: '34px', width: 'auto' }} />
        </Link>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <LanguageSwitcher compact />
          <button onClick={() => setMobileMenuOpen(!mobileMenuOpen)} style={{ padding: '8px', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--color-text-secondary)' }}>
            {mobileMenuOpen ? <X style={{ width: '24px', height: '24px' }} /> : <Menu style={{ width: '24px', height: '24px' }} />}
          </button>
        </div>
      </div>

      {/* Sidebar */}
      <aside style={{
        position: 'fixed', top: 0, left: 0, zIndex: 50, height: '100vh', background: 'var(--color-bg-secondary)', borderRight: '1px solid var(--color-border)',
        width: sidebarOpen ? '260px' : '80px', transition: 'all 0.3s', display: 'flex', flexDirection: 'column',
        transform: mobileMenuOpen ? 'translateX(0)' : 'translateX(-100%)'
      }} className="sidebar-desktop">
        {/* Logo - hide on mobile since mobile header already shows it */} 
        <div style={{ height: '72px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 20px', borderBottom: '1px solid var(--color-border)' }} className="hide-mobile">
          <Link to="/dashboard" style={{ display: 'flex', alignItems: 'center', gap: '12px', textDecoration: 'none', overflow: 'hidden' }}>
            <img src={logoNavbar} alt="SimuTarget" style={{ height: sidebarOpen ? '30px' : '26px', width: 'auto', maxWidth: sidebarOpen ? '190px' : '40px', objectFit: 'contain', objectPosition: 'left', transition: 'all 0.3s' }} />
          </Link>
          <button onClick={() => setSidebarOpen(!sidebarOpen)} style={{ padding: '4px', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--color-text-muted)' }} className="hide-mobile">
            <ChevronLeft style={{ width: '20px', height: '20px', transform: sidebarOpen ? 'none' : 'rotate(180deg)', transition: 'transform 0.3s' }} />
          </button>
        </div>

        {/* Language Switcher in sidebar */}
        {sidebarOpen && (
          <div style={{ padding: '16px 16px 8px 16px' }}>
            <LanguageSwitcher />
          </div>
        )}
        {!sidebarOpen && (
          <div style={{ padding: '12px 0', display: 'flex', justifyContent: 'center' }}>
            <LanguageSwitcher compact />
          </div>
        )}

        {/* Navigation */}
        <nav style={{ flex: 1, padding: '12px 12px', display: 'flex', flexDirection: 'column', gap: '4px', overflowY: 'auto' }}>
          {navItems.map((item) => {
            const Icon = item.icon
            return (
              <Link key={item.href} to={item.href} onClick={() => setMobileMenuOpen(false)}
                style={{
                  display: 'flex', alignItems: 'center', gap: '12px', padding: '12px 16px', borderRadius: '10px', textDecoration: 'none', transition: 'all 0.2s',
                  background: isActive(item.href) ? 'rgba(6, 182, 212, 0.1)' : 'transparent',
                  color: isActive(item.href) ? 'var(--color-accent-cyan)' : 'var(--color-text-secondary)'
                }}>
                <Icon style={{ width: '22px', height: '22px', flexShrink: 0 }} />
                {sidebarOpen && (
                  <>
                    <span style={{ flex: 1, fontSize: '15px', fontWeight: '500' }}>{item.name}</span>
                    {item.badge && <span style={{ padding: '2px 8px', borderRadius: '9999px', fontSize: '11px', fontWeight: '600', background: 'rgba(139, 92, 246, 0.15)', color: 'var(--color-accent-purple)' }}>{item.badge}</span>}
                  </>
                )}
              </Link>
            )
          })}
        </nav>

        {/* Credits */}
        {sidebarOpen && subscription && (
          <div style={{ padding: '16px', borderTop: '1px solid var(--color-border)' }}>
            <div style={{ padding: '16px', borderRadius: '12px', background: 'var(--color-bg-tertiary)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>{t('common.credits')}</span>
                <span style={{ fontSize: '12px', fontWeight: '600' }}>{balance} / {subscription.credits_monthly}</span>
              </div>
              <div style={{ height: '6px', borderRadius: '3px', background: 'var(--color-bg-secondary)', overflow: 'hidden' }}>
                <div className="gradient-bg" style={{ height: '100%', width: `${creditsPercentage}%`, borderRadius: '3px' }} />
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '12px' }}>
                <CreditCard style={{ width: '14px', height: '14px', color: 'var(--color-text-muted)' }} />
                <span style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>{subscription.plan_name} {t('profile.plan')}</span>
              </div>
            </div>
          </div>
        )}

        {/* Bottom */}
        <div style={{ padding: '16px', borderTop: '1px solid var(--color-border)', display: 'flex', flexDirection: 'column', gap: '4px' }}>
          <Link to="/dashboard/profile" onClick={() => setMobileMenuOpen(false)}
            style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '12px 16px', borderRadius: '10px', textDecoration: 'none', color: isActive('/dashboard/profile') ? 'var(--color-accent-cyan)' : 'var(--color-text-secondary)', background: isActive('/dashboard/profile') ? 'rgba(6, 182, 212, 0.1)' : 'transparent' }}>
            <User style={{ width: '22px', height: '22px' }} />
            {sidebarOpen && <span style={{ fontSize: '15px', fontWeight: '500' }}>{t('nav.profile')}</span>}
          </Link>
          <button onClick={handleLogout}
            style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '12px 16px', borderRadius: '10px', width: '100%', border: 'none', cursor: 'pointer', background: 'transparent', color: 'var(--color-danger)', transition: 'background 0.2s' }}>
            <LogOut style={{ width: '22px', height: '22px' }} />
            {sidebarOpen && <span style={{ fontSize: '15px', fontWeight: '500' }}>{t('nav.logout')}</span>}
          </button>
        </div>
      </aside>

      {/* Mobile Overlay */}
      {mobileMenuOpen && <div onClick={() => setMobileMenuOpen(false)} style={{ position: 'fixed', inset: 0, zIndex: 40, background: 'rgba(0,0,0,0.5)' }} className="show-mobile-only" />}

      {/* Main Content */}
      <main style={{ flex: 1, marginLeft: sidebarOpen ? '260px' : '80px', transition: 'margin 0.3s', paddingTop: '0' }} className="main-content">
        <div style={{ padding: '40px' }}>
          {children}
        </div>
      </main>
    </div>
  )
}

export default DashboardLayout