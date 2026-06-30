// ============================================================================
// SimuTarget — <SEO /> bileşeni
// React 19 NATIVE metadata hoisting kullanır: component içinde render edilen
// <title>, <meta>, <link> otomatik olarak <head>'e taşınır. Ek kütüphane YOK.
//
// Kullanım (her public sayfanın en üstünde):
//   import SEO from '../components/SEO'
//   <SEO path="/pricing" />            // routes.js'ten meta'yı çeker
//   <SEO title="..." description="..." />  // manuel override
//
// NOT: Botlar (LinkedIn/X/WhatsApp) JS çalıştırmaz; onlar için asıl meta'yı
// build-time enjeksiyon (scripts/prerender-seo.mjs) sağlar. Bu bileşen Google
// (JS render eder) ve in-app dinamik başlıklar içindir.
// ============================================================================

import { SITE, ROUTE_MAP, ORG_JSONLD } from '../seo/routes'

export default function SEO({
  path,
  title,
  description,
  image,
  noindex,
  jsonLd, // ek sayfa-bazlı JSON-LD objesi (opsiyonel)
}) {
  const meta = (path && ROUTE_MAP[path]) || {}

  const _title = title || meta.title || SITE.defaultTitle
  const _desc = description || meta.description || SITE.defaultDescription
  const _image = image || SITE.ogImage
  const _url = path ? `${SITE.domain}${path === '/' ? '' : path}` : SITE.domain
  const _noindex = noindex ?? (meta.index === false)

  return (
    <>
      <title>{_title}</title>
      <meta name="description" content={_desc} />
      <link rel="canonical" href={_url} />
      {_noindex ? (
        <meta name="robots" content="noindex, nofollow" />
      ) : (
        <meta name="robots" content="index, follow" />
      )}

      {/* Open Graph */}
      <meta property="og:type" content="website" />
      <meta property="og:site_name" content={SITE.name} />
      <meta property="og:title" content={_title} />
      <meta property="og:description" content={_desc} />
      <meta property="og:url" content={_url} />
      <meta property="og:image" content={_image} />
      <meta property="og:image:width" content="1200" />
      <meta property="og:image:height" content="630" />
      <meta property="og:locale" content={SITE.locale} />

      {/* Twitter / X */}
      <meta name="twitter:card" content="summary_large_image" />
      <meta name="twitter:title" content={_title} />
      <meta name="twitter:description" content={_desc} />
      <meta name="twitter:image" content={_image} />
      {SITE.twitterHandle ? <meta name="twitter:site" content={SITE.twitterHandle} /> : null}

      {/* Organization JSON-LD */}
      <script type="application/ld+json">{JSON.stringify(ORG_JSONLD)}</script>
      {jsonLd ? (
        <script type="application/ld+json">{JSON.stringify(jsonLd)}</script>
      ) : null}
    </>
  )
}
