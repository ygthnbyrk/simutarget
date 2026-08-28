"""
Telegram notification service for SimuTarget.

Fire-and-forget pattern: bildirim hatası asıl iş akışını bozmaz.
Production'da TELEGRAM_ENABLED env var ile açılır/kapatılır (kill switch).

Yer: backend/src/services/notification_service.py
Convention: lemonsqueezy_service.py ile aynı

Kullanım:
    from src.services.notification_service import notify_new_user
    notify_new_user(email="a@b.com", user_id=42, total_users=100)
"""
import asyncio
import logging
import os
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

import httpx

logger = logging.getLogger(__name__)

# ============================================
# CONFIG (env vars)
# ============================================

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
TELEGRAM_ENABLED = os.getenv("TELEGRAM_ENABLED", "false").lower() == "true"

TR_TZ = ZoneInfo("Europe/Istanbul")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"


# ============================================
# LOW-LEVEL SENDER
# ============================================

def _now_tr() -> str:
    """Turkish locale-friendly timestamp."""
    return datetime.now(TR_TZ).strftime("%d %b %Y, %H:%M")


async def _send_raw(text: str) -> None:
    """
    Düşük seviyeli gönderim.

    HATA YUTAR — bildirim altyapısı çökse bile asıl business logic etkilenmez.
    Tüm hatalar log'a düşer.
    """
    if not TELEGRAM_ENABLED:
        return
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram env vars eksik, bildirim atlandı.")
        return

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(
                TELEGRAM_API_URL,
                json={
                    "chat_id": TELEGRAM_CHAT_ID,
                    "text": text,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True,
                },
            )
            if resp.status_code != 200:
                logger.error(
                    f"Telegram hata: {resp.status_code} {resp.text[:300]}"
                )
    except Exception as e:
        logger.error(f"Telegram gönderim hatası: {e}")


def send_async(text: str) -> None:
    """
    Fire-and-forget wrapper.

    Çağıran await beklemez — task background'a düşer.

    İki context'i de destekler:
      - Async endpoint (event loop var) → loop.create_task
      - Sync endpoint / threadpool (event loop yok) → daemon thread'de asyncio.run

    Her iki durumda da caller blocking değil.
    """
    if not TELEGRAM_ENABLED:
        return

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_send_raw(text))
    except RuntimeError:
        # Running loop yok (FastAPI'de sync `def` endpoint → threadpool).
        # Daemon thread'de yeni loop'ta çalıştır.
        import threading
        threading.Thread(
            target=lambda: asyncio.run(_send_raw(text)),
            daemon=True,
        ).start()


# ============================================
# HIGH-LEVEL EVENT HELPERS
# ============================================

def notify_new_user(
    email: str,
    user_id: int,
    name: Optional[str] = None,
    total_users: Optional[int] = None,
) -> None:
    """Yeni kullanıcı kaydı bildirimi."""
    lines = [
        "🎉 <b>Yeni üye</b>",
        f"📧 {email}",
    ]
    if name:
        lines.append(f"👤 {name}")
    lines.append(f"🆔 #{user_id}")
    if total_users is not None:
        lines.append(f"👥 Toplam üye: <b>{total_users}</b>")
    lines.append(f"🕐 {_now_tr()}")
    send_async("\n".join(lines))


def notify_new_subscription(
    email: str,
    plan: str,
    amount_usd: Optional[float] = None,
    subscription_id: Optional[str] = None,
    is_renewal: bool = False,
) -> None:
    """Yeni abonelik veya renewal bildirimi."""
    emoji = "🔁" if is_renewal else "💰"
    title = "Abonelik yenilendi" if is_renewal else "Yeni abonelik"
    lines = [
        f"{emoji} <b>{title}</b>",
        f"📧 {email}",
        f"📦 Plan: <b>{plan}</b>",
    ]
    if amount_usd is not None and amount_usd > 0:
        lines.append(f"💵 ${amount_usd:.2f}")
    if subscription_id:
        lines.append(f"🆔 <code>sub_{subscription_id}</code>")
    lines.append(f"🕐 {_now_tr()}")
    send_async("\n".join(lines))


def notify_one_time_payment(
    email: str,
    product: str,
    amount_usd: Optional[float] = None,
    order_id: Optional[str] = None,
) -> None:
    """Tek seferlik ödeme bildirimi (Disposable test pack vs.)."""
    lines = [
        "💳 <b>Tek seferlik ödeme</b>",
        f"📧 {email}",
        f"📦 {product}",
    ]
    if amount_usd is not None and amount_usd > 0:
        lines.append(f"💵 ${amount_usd:.2f}")
    if order_id:
        lines.append(f"🆔 <code>order_{order_id}</code>")
    lines.append(f"🕐 {_now_tr()}")
    send_async("\n".join(lines))


def notify_subscription_cancelled(
    email: str,
    plan: str,
    subscription_id: Optional[str] = None,
    ends_at: Optional[datetime] = None,
) -> None:
    """Abonelik iptal bildirimi (churn alarmı)."""
    lines = [
        "⚠️ <b>Abonelik iptali</b>",
        f"📧 {email}",
        f"📦 Plan: {plan}",
    ]
    if subscription_id:
        lines.append(f"🆔 <code>sub_{subscription_id}</code>")
    if ends_at:
        lines.append(f"🗓️ Erişim son: {ends_at.strftime('%d %b %Y')}")
    lines.append(f"🕐 {_now_tr()}")
    send_async("\n".join(lines))


def notify_payment_failed(
    email: str,
    plan: str,
    subscription_id: Optional[str] = None,
) -> None:
    """Ödeme başarısız (past_due) — kullanıcı kartı güncelleyene kadar."""
    lines = [
        "🔴 <b>Ödeme başarısız</b>",
        f"📧 {email}",
        f"📦 Plan: {plan}",
    ]
    if subscription_id:
        lines.append(f"🆔 <code>sub_{subscription_id}</code>")
    lines.append(f"🕐 {_now_tr()}")
    send_async("\n".join(lines))


def notify_refund(
    email: str,
    amount_usd: float,
    order_id: Optional[str] = None,
) -> None:
    """Para iadesi bildirimi."""
    lines = [
        "↩️ <b>Para iadesi</b>",
        f"📧 {email}",
        f"💵 ${amount_usd:.2f}",
    ]
    if order_id:
        lines.append(f"🆔 <code>order_{order_id}</code>")
    lines.append(f"🕐 {_now_tr()}")
    send_async("\n".join(lines))


def notify_error(context: str, error: str) -> None:
    """Kritik sistem hataları için manual trigger."""
    lines = [
        "🚨 <b>SİSTEM HATASI</b>",
        f"📍 {context}",
        f"❌ <code>{error[:500]}</code>",
        f"🕐 {_now_tr()}",
    ]
    send_async("\n".join(lines))


def notify_startup(env: str = "production") -> None:
    """Backend startup'ta — deploy başarısını anında görmek için."""
    lines = [
        "🟢 <b>Backend ayakta</b>",
        f"🌐 Env: {env}",
        f"🕐 {_now_tr()}",
    ]
    send_async("\n".join(lines))
