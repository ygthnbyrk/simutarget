// ============================================================================
// SimuTarget — Build-time SEO prerender (head injection + sitemap)
// `vite build` SONRASI çalışır. Router'a / React koduna DOKUNMAZ.
//
// Ne yapar:
//   1. dist/index.html'i şablon alır.
//   2. Her indexable rota için dist/<rota>/index.html üretir; her birinin
//      <title>, description, canonical, OG, Twitter, JSON-LD'si rotaya özeldir.
//      → Botlar (LinkedIn/X/WhatsApp) doğru per-route önizlemeyi görür.
//   3. dist/sitemap.xml'i ROUTES'tan üretir (sadece index:true olanlar).
//
// package.json:  "build": "vite build && node scripts/prerender-seo.mjs"
// Ek bağımlılık YOK (saf node fs + string/regex).
// ============================================================================

import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { SITE, ROUTES, ORG_JSONLD } from '../src/seo/routes.js'

const __dirname = dirname(fileURLToPath(import.meta.url))
const DIST = join(__dirname, '..', 'dist')
const INDEX = join(DIST, 'index.html')

if (!existsSync(INDEX)) {
  console.error('[prerender-seo] dist/index.html yok — önce `vite build` çalışmalı.')
  process.exit(1)
}

const template = readFileSync(INDEX, 'utf8')
const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')

// Şablondan değişken head etiketlerini temizle (her rotada yeniden basacağız)
function stripDynamicHead(html) {
  return html
    .replace(/<title>[\s\S]*?<\/title>/i, '')
    .replace(/<meta\s+name=["']description["'][^>]*>/gi, '')
    .replace(/<meta\s+name=["']robots["'][^>]*>/gi, '')
    .replace(/<link\s+rel=["']canonical["'][^>]*>/gi, '')
    .replace(/<meta\s+property=["']og:[^"']*["'][^>]*>/gi, '')
    .replace(/<meta\s+name=["']twitter:[^"']*["'][^>]*>/gi, '')
    .replace(/<script\s+type=["']application\/ld\+json["'][^>]*>[\s\S]*?<\/script>/gi, '')
}

function headBlock(route) {
  const url = `${SITE.domain}${route.path === '/' ? '' : route.path}`
  const noindex = route.index === false
  const tags = [
    `<title>${esc(route.title)}</title>`,
    `<meta name="description" content="${esc(route.description)}" />`,
    `<link rel="canonical" href="${url}" />`,
    `<meta name="robots" content="${noindex ? 'noindex, nofollow' : 'index, follow'}" />`,
    `<meta property="og:type" content="website" />`,
    `<meta property="og:site_name" content="${esc(SITE.name)}" />`,
    `<meta property="og:title" content="${esc(route.title)}" />`,
    `<meta property="og:description" content="${esc(route.description)}" />`,
    `<meta property="og:url" content="${url}" />`,
    `<meta property="og:image" content="${SITE.ogImage}" />`,
    `<meta property="og:image:width" content="1200" />`,
    `<meta property="og:image:height" content="630" />`,
    `<meta property="og:locale" content="${SITE.locale}" />`,
    `<meta name="twitter:card" content="summary_large_image" />`,
    `<meta name="twitter:title" content="${esc(route.title)}" />`,
    `<meta name="twitter:description" content="${esc(route.description)}" />`,
    `<meta name="twitter:image" content="${SITE.ogImage}" />`,
    `<script type="application/ld+json">${JSON.stringify(ORG_JSONLD)}</script>`,
  ]
  if (SITE.twitterHandle) tags.push(`<meta name="twitter:site" content="${esc(SITE.twitterHandle)}" />`)
  return tags.join('\n    ')
}

function buildHtml(route) {
  const stripped = stripDynamicHead(template)
  return stripped.replace(/<\/head>/i, `    ${headBlock(route)}\n  </head>`)
}

let count = 0
for (const route of ROUTES) {
  const html = buildHtml(route)
  if (route.path === '/') {
    writeFileSync(INDEX, html)
  } else {
    const dir = join(DIST, route.path.replace(/^\//, ''))
    mkdirSync(dir, { recursive: true })
    writeFileSync(join(dir, 'index.html'), html)
  }
  count++
}

// sitemap.xml — sadece indexable rotalar
const today = new Date().toISOString().slice(0, 10)
const urls = ROUTES.filter((r) => r.index).map((r) => {
  const loc = `${SITE.domain}${r.path === '/' ? '/' : r.path}`
  return `  <url>
    <loc>${loc}</loc>
    <lastmod>${today}</lastmod>
    <changefreq>${r.changefreq || 'monthly'}</changefreq>
    <priority>${(r.priority ?? 0.5).toFixed(1)}</priority>
  </url>`
}).join('\n')
const sitemap = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${urls}
</urlset>
`
writeFileSync(join(DIST, 'sitemap.xml'), sitemap)

console.log(`[prerender-seo] ${count} rota için head enjekte edildi, sitemap.xml üretildi (${ROUTES.filter(r=>r.index).length} URL).`)
