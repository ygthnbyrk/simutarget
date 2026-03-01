import PublicNavbar from './layout/PublicNavbar'
import Footer from './layout/Footer'

function LegalPageLayout({ children }) {
  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', background: 'var(--color-bg-primary)' }}>
      <PublicNavbar />
      <main style={{ flex: 1, paddingTop: '100px', paddingBottom: '80px' }}>
        <div style={{ maxWidth: '860px', margin: '0 auto', padding: '0 24px' }}>
          {children}
        </div>
      </main>
      <Footer />
    </div>
  )
}

export default LegalPageLayout