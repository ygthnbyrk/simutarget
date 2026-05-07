"""
Lemon Squeezy API Client.

LS'a karşı API call'ları yapar (checkout oluşturma, customer/subscription yönetimi)
ve webhook signature doğrulaması yapar.

API dokümantasyon: https://docs.lemonsqueezy.com/api
"""
import os
import hmac
import hashlib
import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


# ============================================
# CONFIG (env'den okunur)
# ============================================

LEMONSQUEEZY_API_KEY = os.getenv("LEMONSQUEEZY_API_KEY", "")
LEMONSQUEEZY_STORE_ID = os.getenv("LEMONSQUEEZY_STORE_ID", "")
LEMONSQUEEZY_WEBHOOK_SECRET = os.getenv("LEMONSQUEEZY_WEBHOOK_SECRET", "")

# LS API base URL — sandbox/production ayrımı yok, test mode store-level toggle
LEMONSQUEEZY_API_BASE = "https://api.lemonsqueezy.com/v1"


# ============================================
# CUSTOM EXCEPTIONS
# ============================================

class LemonSqueezyError(Exception):
    """Genel Lemon Squeezy hatası."""
    pass


class LemonSqueezySignatureError(LemonSqueezyError):
    """Webhook signature doğrulanamadı."""
    pass


class LemonSqueezyAPIError(LemonSqueezyError):
    """LS API HTTP hatası."""
    def __init__(self, status_code: int, message: str, response_body: dict = None):
        self.status_code = status_code
        self.response_body = response_body or {}
        super().__init__(f"Lemon Squeezy API error {status_code}: {message}")


# ============================================
# WEBHOOK SIGNATURE VERIFICATION
# ============================================

def verify_webhook_signature(
    raw_body: bytes,
    signature_header: str,
    secret: Optional[str] = None,
) -> bool:
    """
    Lemon Squeezy webhook signature'ını doğrular.

    LS her webhook'ta `X-Signature` header'ı gönderir, format:
        deadbeef0123456789abcdef...   (sadece hex string, başka bir şey yok)

    Paddle'dan farkı:
      - Paddle: ts=...;h1=...  (timestamp + HMAC)
      - LS: sadece HMAC hex (timestamp yok)

    Doğrulama:
      1. HMAC-SHA256(raw_body, secret) hesapla
      2. X-Signature header'ı ile constant-time karşılaştır

    Args:
        raw_body: Webhook'un raw HTTP body'si (bytes)
        signature_header: `X-Signature` header değeri (hex string)
        secret: Webhook signing secret (None ise env'den okunur)

    Returns:
        True if valid, False otherwise.

    Raises:
        LemonSqueezySignatureError: Signature missing veya secret eksik.
    """
    if secret is None:
        secret = LEMONSQUEEZY_WEBHOOK_SECRET

    if not secret:
        raise LemonSqueezySignatureError(
            "LEMONSQUEEZY_WEBHOOK_SECRET env değişkeni boş. "
            "LS dashboard → Settings → Webhooks → mevcut webhook'taki "
            "signing secret ile aynı olmalı."
        )

    if not signature_header:
        raise LemonSqueezySignatureError("X-Signature header eksik.")

    # HMAC hesapla — payload doğrudan raw_body, timestamp prefix yok
    expected = hmac.new(
        secret.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()

    # Constant-time karşılaştırma
    return hmac.compare_digest(expected, signature_header.strip())


# ============================================
# LEMON SQUEEZY API CLIENT (async)
# ============================================

class LemonSqueezyClient:
    """
    Async Lemon Squeezy API client.

    Kullanım:
        async with LemonSqueezyClient() as client:
            checkout = await client.create_checkout(...)
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or LEMONSQUEEZY_API_KEY
        if not self.api_key:
            raise LemonSqueezyError(
                "LEMONSQUEEZY_API_KEY env değişkeni boş. "
                "LS dashboard → Settings → API → 'Create API key' ile al."
            )
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        self._client = httpx.AsyncClient(
            base_url=LEMONSQUEEZY_API_BASE,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/vnd.api+json",
                "Content-Type": "application/vnd.api+json",
            },
            timeout=30.0,
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()

    async def _request(self, method: str, path: str, **kwargs) -> dict:
        """Internal HTTP request helper."""
        if not self._client:
            raise LemonSqueezyError("LemonSqueezyClient context manager dışında kullanıldı.")

        response = await self._client.request(method, path, **kwargs)

        if response.status_code >= 400:
            body = {}
            try:
                body = response.json()
            except Exception:
                pass

            # LS error format: {"errors": [{"detail": "...", "status": "...", "title": "..."}]}
            errors = body.get("errors", [])
            error_msg = errors[0].get("detail") if errors else response.text

            raise LemonSqueezyAPIError(
                response.status_code,
                error_msg,
                body,
            )

        # 204 No Content (DELETE response gibi) için boş dict
        if response.status_code == 204:
            return {}

        return response.json()

    # ========================================
    # CHECKOUTS (frontend için checkout URL)
    # ========================================

    async def create_checkout(
        self,
        variant_id: str,
        user_email: str,
        user_name: Optional[str] = None,
        custom_data: Optional[dict] = None,
        store_id: Optional[str] = None,
        redirect_url: Optional[str] = None,
        embed: bool = True,
    ) -> dict:
        """
        LS checkout oluştur. Frontend bu URL'i Lemon.js overlay ile açar.

        LS Paddle'dan farklı: önce customer yaratmaya gerek yok. LS checkout
        sırasında email ile otomatik customer oluşturur. customer_id webhook'ta
        gelir, sonra User'a kaydederiz.

        Args:
            variant_id: LS variant ID (sayı, örn "12345")
            user_email: Müşteri email'i (LS bu email ile customer açar)
            user_name: Müşteri adı (opsiyonel)
            custom_data: Webhook'ta geri gelecek metadata (örn. {"user_id": "123", "plan_slug": "pro"})
            store_id: LS store ID (None ise env'den)
            redirect_url: Ödeme sonrası yönlendirilecek URL (overlay close fallback)
            embed: True = Lemon.js overlay için, False = full page redirect için

        Returns: {id, url, expires_at}
        """
        store_id = store_id or LEMONSQUEEZY_STORE_ID
        if not store_id:
            raise LemonSqueezyError(
                "LEMONSQUEEZY_STORE_ID env değişkeni boş. "
                "LS dashboard → Settings → Stores → store ID'yi al."
            )

        # Custom data değerlerini string'e çevir (LS JSON:API string bekler)
        normalized_custom = None
        if custom_data:
            normalized_custom = {k: str(v) for k, v in custom_data.items()}

        checkout_data: dict = {"email": user_email}
        if user_name:
            checkout_data["name"] = user_name
        if normalized_custom:
            checkout_data["custom"] = normalized_custom

        product_options: dict = {}
        if redirect_url:
            product_options["redirect_url"] = redirect_url

        payload = {
            "data": {
                "type": "checkouts",
                "attributes": {
                    "checkout_data": checkout_data,
                    "checkout_options": {
                        "embed": embed,
                        "media": False,
                        "logo": True,
                    },
                    "product_options": product_options,
                },
                "relationships": {
                    "store": {
                        "data": {"type": "stores", "id": str(store_id)},
                    },
                    "variant": {
                        "data": {"type": "variants", "id": str(variant_id)},
                    },
                },
            }
        }

        result = await self._request("POST", "/checkouts", json=payload)
        data = result.get("data", {})
        attrs = data.get("attributes", {})
        return {
            "id": data.get("id"),
            "url": attrs.get("url"),
            "expires_at": attrs.get("expires_at"),
        }

    # ========================================
    # CUSTOMERS
    # ========================================

    async def get_customer(self, customer_id: str) -> dict:
        """Customer detayı (urls.customer_portal dahil)."""
        result = await self._request("GET", f"/customers/{customer_id}")
        return result.get("data", {})

    async def find_customer_by_email(self, email: str) -> Optional[dict]:
        """Email ile customer ara, varsa döndür, yoksa None."""
        result = await self._request(
            "GET",
            "/customers",
            params={"filter[email]": email},
        )
        customers = result.get("data", [])
        return customers[0] if customers else None

    async def get_customer_portal_url(self, customer_id: str) -> str:
        """
        Customer'ın portal URL'i.

        Bu URL kullanıcı 'Manage subscription' butonuna basınca yönlendirilen
        yer — orada subscription'ını yönetir, fatura indirir, kart günceller.

        LS'de portal URL uzun ömürlü, customer'ın kendi attribute'unda gelir.
        Paddle'da olduğu gibi her seferinde yeni session oluşturmaya gerek yok.
        """
        customer = await self.get_customer(customer_id)
        urls = customer.get("attributes", {}).get("urls", {}) or {}
        portal_url = urls.get("customer_portal", "")
        if not portal_url:
            raise LemonSqueezyError(
                f"Customer {customer_id} için portal URL bulunamadı. "
                "Customer henüz subscription almamış olabilir."
            )
        return portal_url

    # ========================================
    # SUBSCRIPTIONS
    # ========================================

    async def get_subscription(self, subscription_id: str) -> dict:
        """Subscription detayı."""
        result = await self._request("GET", f"/subscriptions/{subscription_id}")
        return result.get("data", {})

    async def cancel_subscription(self, subscription_id: str) -> dict:
        """
        Subscription iptal et.

        LS'de DELETE çağrısı = iptal. Anında kesilmez — subscription dönem
        sonuna kadar aktif kalır (status='cancelled' ama is_active hala true),
        sonra otomatik 'expired' olur.

        Bu davranış Paddle'ın 'effective_from=next_billing_period' ile aynı.
        """
        result = await self._request("DELETE", f"/subscriptions/{subscription_id}")
        return result.get("data", {})

    async def resume_subscription(self, subscription_id: str) -> dict:
        """
        İptal edilmiş subscription'ı geri al (cancelled → active).
        Sadece dönem henüz bitmediyse mümkün.
        """
        payload = {
            "data": {
                "type": "subscriptions",
                "id": str(subscription_id),
                "attributes": {
                    "cancelled": False,
                },
            }
        }
        result = await self._request(
            "PATCH",
            f"/subscriptions/{subscription_id}",
            json=payload,
        )
        return result.get("data", {})
