// ============================================================================
// SimuTarget — SEO route metadata (TEK DOĞRULUK KAYNAĞI)
// Bu dosya üç yerde kullanılır:
//   1. src/components/SEO.jsx        → runtime <head> (React 19 native metadata)
//   2. scripts/prerender-seo.mjs     → build-time per-route static <head> enjeksiyonu
//   3. scripts/prerender-seo.mjs     → sitemap.xml üretimi
// Yeni public sayfa eklerken SADECE burayı güncelle.
// ============================================================================

export const SITE = {
  domain: 'https://simutarget.ai',
  name: 'SimuTarget',
  defaultTitle: 'SimuTarget — AI Synthetic Market Research & Audience Testing',
  defaultDescription:
    'Test campaigns and creative against 500K+ AI consumer personas before launch. Synthetic market research in minutes — no panels, no privacy risk.',
  ogImage: 'https://simutarget.ai/og-default.png',
  twitterHandle: '', // örn. '@simutarget' — varsa doldur
  locale: 'en_US',
}

// path           : rota (App.jsx ile birebir)
// title          : <title> (benzersiz)
// description    : meta description (~150-160 karakter)
// index          : true → indekslensin & sitemap'e girsin | false → noindex
// changefreq/priority : sitemap hint'leri
export const ROUTES = [
  {
    path: '/',
    title: 'SimuTarget — AI Synthetic Market Research & Audience Testing',
    description:
      'Test campaigns and creative against 500K+ AI consumer personas before launch. Synthetic market research in minutes — no panels, no privacy risk.',
    index: true,
    changefreq: 'weekly',
    priority: 1.0,
  },
  {
    path: '/pricing',
    title: 'Pricing — SimuTarget',
    description:
      'Simple credit-based plans for synthetic market research. Run single tests, A/B comparisons, and multi-variant studies against AI consumer personas.',
    index: true,
    changefreq: 'weekly',
    priority: 0.9,
  },
  {
    path: '/about',
    title: 'About SimuTarget — Synthetic Audience Simulation',
    description:
      'SimuTarget simulates real consumer behavior with AI personas, so brands and agencies can validate campaigns before spending media budget.',
    index: true,
    changefreq: 'monthly',
    priority: 0.6,
  },
  {
    path: '/contact',
    title: 'Contact — SimuTarget',
    description:
      'Get in touch with the SimuTarget team about synthetic market research, enterprise plans, or partnerships.',
    index: true,
    changefreq: 'monthly',
    priority: 0.5,
  },
  {
    path: '/faqs',
    title: 'FAQ — SimuTarget',
    description:
      'Answers to common questions about SimuTarget: how synthetic personas work, accuracy, pricing, credits, and data privacy.',
    index: true,
    changefreq: 'monthly',
    priority: 0.6,
  },
  {
    path: '/partner',
    title: 'Partner with SimuTarget',
    description:
      'Partner with SimuTarget to bring AI-powered synthetic market research to your agency or client base.',
    index: true,
    changefreq: 'monthly',
    priority: 0.5,
  },
  {
    path: '/terms',
    title: 'Terms & Conditions — SimuTarget',
    description: 'The terms and conditions governing use of the SimuTarget platform.',
    index: true,
    changefreq: 'yearly',
    priority: 0.3,
  },
  {
    path: '/privacy',
    title: 'Privacy Policy — SimuTarget',
    description: 'How SimuTarget collects, uses, and protects your data.',
    index: true,
    changefreq: 'yearly',
    priority: 0.3,
  },
  {
    path: '/cookies',
    title: 'Cookie Policy — SimuTarget',
    description: 'How SimuTarget uses cookies and similar technologies.',
    index: true,
    changefreq: 'yearly',
    priority: 0.3,
  },
  {
    path: '/refund',
    title: 'Refund Policy — SimuTarget',
    description: 'SimuTarget refund and cancellation policy for subscriptions and credits.',
    index: true,
    changefreq: 'yearly',
    priority: 0.3,
  },

  // --- noindex (auth / thin) — sitemap'e GİRMEZ ---
  { path: '/login', title: 'Log in — SimuTarget', description: 'Log in to your SimuTarget account.', index: false },
  { path: '/register', title: 'Sign up — SimuTarget', description: 'Create your SimuTarget account.', index: false },
]

// Path → meta lookup (SEO.jsx runtime kullanımı için)
export const ROUTE_MAP = Object.fromEntries(ROUTES.map((r) => [r.path, r]))

// Organization JSON-LD (her sayfada head'e eklenir)
export const ORG_JSONLD = {
  '@context': 'https://schema.org',
  '@type': 'Organization',
  name: 'SimuTarget',
  url: SITE.domain,
  logo: `${SITE.domain}/icon-512.png`,
  description: SITE.defaultDescription,
}
