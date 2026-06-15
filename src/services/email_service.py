"""
Resend email service for SimuTarget.

Fire-and-forget pattern (notification_service.py ile birebir aynı):
email hatası asıl iş akışını bozmaz. EMAIL_ENABLED env var ile kill switch.

Yer: src/services/email_service.py
Convention: notification_service.py, lemonsqueezy_service.py ile aynı

Kullanım:
    from src.services.email_service import send_password_reset_email
    send_password_reset_email(to_email="a@b.com", name="Ali", reset_url="https://...")

NOT (domain doğrulama): RESEND_FROM_EMAIL'in @simutarget.ai adresini
kullanabilmek için Resend'de domain doğrulanmış olmalı (DKIM/SPF DNS kayıtları).
Doğrulama yapılana kadar sadece "onboarding@resend.dev" adresinden gönderilebilir.
"""
import asyncio
import logging
import os
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# ============================================
# CONFIG (env vars)
# ============================================

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
# Domain doğrulanana kadar: "SimuTarget <onboarding@resend.dev>"
# Doğrulandıktan sonra: "SimuTarget <noreply@simutarget.ai>"
RESEND_FROM_EMAIL = os.getenv("RESEND_FROM_EMAIL", "SimuTarget <onboarding@resend.dev>")
EMAIL_ENABLED = os.getenv("EMAIL_ENABLED", "true").lower() == "true"

RESEND_API_URL = "https://api.resend.com/emails"


# ============================================
# LOW-LEVEL SENDER
# ============================================

async def _send_raw(to_email: str, subject: str, html: str) -> None:
    """
    Düşük seviyeli gönderim.

    HATA YUTAR — email altyapısı çökse bile asıl business logic etkilenmez.
    Tüm hatalar log'a düşer.
    """
    if not EMAIL_ENABLED:
        return
    if not RESEND_API_KEY:
        logger.warning("RESEND_API_KEY tanımlı değil, email atlandı.")
        return

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                RESEND_API_URL,
                headers={
                    "Authorization": f"Bearer {RESEND_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "from": RESEND_FROM_EMAIL,
                    "to": [to_email],
                    "subject": subject,
                    "html": html,
                },
            )
            if resp.status_code >= 300:
                logger.error(
                    f"Resend hata: {resp.status_code} {resp.text[:300]}"
                )
    except Exception as e:
        logger.error(f"Resend gönderim hatası: {e}")


def send_async(to_email: str, subject: str, html: str) -> None:
    """
    Fire-and-forget wrapper (notification_service.send_async ile aynı mantık).

    Çağıran await beklemez. Async endpoint'te loop.create_task,
    sync endpoint / threadpool'da daemon thread'de asyncio.run.
    """
    if not EMAIL_ENABLED:
        return

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_send_raw(to_email, subject, html))
    except RuntimeError:
        # Running loop yok (FastAPI'de sync `def` endpoint → threadpool).
        import threading
        threading.Thread(
            target=lambda: asyncio.run(_send_raw(to_email, subject, html)),
            daemon=True,
        ).start()


# ============================================
# HTML TEMPLATE
# ============================================

def _password_reset_html(name: Optional[str], reset_url: str) -> str:
    """Şifre sıfırlama email gövdesi (Türkçe, email-client uyumlu inline CSS)."""
    greeting = f"Merhaba {name}," if name else "Merhaba,"
    return f"""\
<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin:0;padding:0;background-color:#f4f4f7;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f4f7;padding:32px 0;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:480px;background-color:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,0.08);">
          <!-- Header -->
          <tr>
            <td style="background-color:#0f172a;padding:24px 32px;">
              <span style="color:#ffffff;font-size:20px;font-weight:700;letter-spacing:-0.02em;">SimuTarget</span>
            </td>
          </tr>
          <!-- Body -->
          <tr>
            <td style="padding:32px;">
              <p style="margin:0 0 16px;font-size:16px;color:#0f172a;">{greeting}</p>
              <p style="margin:0 0 16px;font-size:15px;line-height:1.6;color:#334155;">
                Hesabınız için bir şifre sıfırlama talebi aldık. Yeni şifrenizi belirlemek için
                aşağıdaki butona tıklayın.
              </p>
              <table role="presentation" cellpadding="0" cellspacing="0" style="margin:24px 0;">
                <tr>
                  <td align="center" style="border-radius:8px;background-color:#4f46e5;">
                    <a href="{reset_url}" target="_blank"
                       style="display:inline-block;padding:14px 28px;font-size:15px;font-weight:600;color:#ffffff;text-decoration:none;border-radius:8px;">
                      Şifremi Sıfırla
                    </a>
                  </td>
                </tr>
              </table>
              <p style="margin:0 0 16px;font-size:13px;line-height:1.6;color:#64748b;">
                Buton çalışmazsa bu bağlantıyı tarayıcınıza yapıştırın:<br>
                <a href="{reset_url}" target="_blank" style="color:#4f46e5;word-break:break-all;">{reset_url}</a>
              </p>
              <p style="margin:0 0 8px;font-size:13px;line-height:1.6;color:#64748b;">
                Bu bağlantı <strong>1 saat</strong> boyunca geçerlidir.
              </p>
              <p style="margin:0;font-size:13px;line-height:1.6;color:#64748b;">
                Bu talebi siz yapmadıysanız bu e-postayı yok sayabilirsiniz; şifreniz değişmez.
              </p>
            </td>
          </tr>
          <!-- Footer -->
          <tr>
            <td style="padding:20px 32px;border-top:1px solid #e2e8f0;">
              <p style="margin:0;font-size:12px;color:#94a3b8;">
                © SimuTarget — AI destekli sentetik pazar araştırması
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


# ============================================
# HIGH-LEVEL EVENT HELPERS
# ============================================

def send_password_reset_email(to_email: str, name: Optional[str], reset_url: str) -> None:
    """Şifre sıfırlama bağlantısı emaili (fire-and-forget)."""
    subject = "SimuTarget — Şifre Sıfırlama"
    html = _password_reset_html(name, reset_url)
    send_async(to_email, subject, html)
