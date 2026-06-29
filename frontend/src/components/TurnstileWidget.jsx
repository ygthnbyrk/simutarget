// frontend/src/components/TurnstileWidget.jsx
// Cloudflare Turnstile — paylaşılan widget bileşeni (oturum #9.0)
//
// Kullanım:
//   const [token, setToken] = useState('')
//   const tsRef = useRef(null)
//   <TurnstileWidget ref={tsRef} onVerify={setToken} />
//   ... submit sonrası: tsRef.current?.reset()
//
// Notlar:
//   - onVerify olarak STABİL bir setter geç (örn. useState setter). Her render'da
//     değişen inline fonksiyon geçilirse widget gereksiz yere yeniden render edilir.
//   - VITE_TURNSTILE_SITE_KEY tanımlı değilse bileşen hiçbir şey çizmez (no-op);
//     bu durumda parent form token istememeli (backend de secret yoksa atlar).
//   - Turnstile token'ları tek kullanımlık + 300sn ömürlü. Başarısız submit
//     sonrası reset() ile taze token alınır.
import { useEffect, useRef, forwardRef, useImperativeHandle } from 'react'

const SITE_KEY = import.meta.env.VITE_TURNSTILE_SITE_KEY
const SCRIPT_ID = 'cf-turnstile-script'
const SCRIPT_SRC = 'https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit'

function loadTurnstileScript() {
  return new Promise((resolve, reject) => {
    if (window.turnstile) {
      resolve()
      return
    }
    const existing = document.getElementById(SCRIPT_ID)
    if (existing) {
      existing.addEventListener('load', () => resolve())
      existing.addEventListener('error', () => reject(new Error('Turnstile yüklenemedi')))
      return
    }
    const script = document.createElement('script')
    script.id = SCRIPT_ID
    script.src = SCRIPT_SRC
    script.async = true
    script.defer = true
    script.onload = () => resolve()
    script.onerror = () => reject(new Error('Turnstile yüklenemedi'))
    document.head.appendChild(script)
  })
}

const TurnstileWidget = forwardRef(function TurnstileWidget({ onVerify, theme = 'auto' }, ref) {
  const containerRef = useRef(null)
  const widgetIdRef = useRef(null)

  useImperativeHandle(ref, () => ({
    reset: () => {
      if (window.turnstile && widgetIdRef.current !== null) {
        try {
          window.turnstile.reset(widgetIdRef.current)
        } catch (_) {
          /* yoksay */
        }
      }
    },
  }))

  useEffect(() => {
    if (!SITE_KEY) return // özellik yapılandırılmamış — no-op

    let cancelled = false

    loadTurnstileScript()
      .then(() => {
        if (cancelled || !containerRef.current || !window.turnstile) return
        if (widgetIdRef.current !== null) return // zaten render edilmiş
        widgetIdRef.current = window.turnstile.render(containerRef.current, {
          sitekey: SITE_KEY,
          theme,
          callback: (token) => onVerify?.(token),
          'expired-callback': () => onVerify?.(''),
          'error-callback': () => onVerify?.(''),
        })
      })
      .catch(() => {
        // Script yüklenemezse sessizce geç; submit anında token yoksa
        // parent kullanıcıyı buton disable ile bekletir.
      })

    return () => {
      cancelled = true
      if (window.turnstile && widgetIdRef.current !== null) {
        try {
          window.turnstile.remove(widgetIdRef.current)
        } catch (_) {
          /* yoksay */
        }
        widgetIdRef.current = null
      }
    }
  }, [onVerify, theme])

  if (!SITE_KEY) return null

  return (
    <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '24px' }}>
      <div ref={containerRef} />
    </div>
  )
})

export default TurnstileWidget
