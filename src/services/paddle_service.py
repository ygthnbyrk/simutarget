"""
Paddle Billing API Client.

Paddle'a karşı API call'ları yapar (transaction oluşturma, customer yönetimi,
subscription cancel vb.) ve webhook signature doğrulaması yapar.

API dokümantasyon: https://developer.paddle.com/api-reference/overview
"""
import os
import hmac
import hashlib
import logging
from typing import Optional
from datetime import datetime

import httpx

logger = logging.getLogger(__name__)


# ============================================
# CONFIG (env'den okunur)
# ============================================

PADDLE_API_KEY = os.getenv("PADDLE_API_KEY", "")
PADDLE_WEBHOOK_SECRET = os.getenv("PADDLE_WEBHOOK_SECRET", "")
PADDLE_ENVIRONMENT = os.getenv("PADDLE_ENVIRONMENT", "production").lower()

# API base URL — environment'a göre
if PADDLE_ENVIRONMENT == "sandbox":
    PADDLE_API_BASE = "https://sandbox-api.paddle.com"
else:
    PADDLE_API_BASE = "https://api.paddle.com"

# Webhook signature timestamp tolerance (saniye)
WEBHOOK_TIMESTAMP_TOLERANCE = 300  # 5 dakika


# ============================================
# CUSTOM EXCEPTIONS
# ============================================

class PaddleError(Exception):
    """Genel Paddle hatası."""
    pass


class PaddleSignatureError(PaddleError):
    """Webhook signature doğrulanamadı."""
    pass


class PaddleAPIError(PaddleError):
    """Paddle API HTTP hatası."""
    def __init__(self, status_code: int, message: str, response_body: dict = None):
        self.status_code = status_code
        self.response_body = response_body or {}
        super().__init__(f"Paddle API error {status_code}: {message}")


# ============================================
# WEBHOOK SIGNATURE VERIFICATION
# ============================================

def verify_webhook_signature(
    raw_body: bytes,
    signature_header: str,
    secret: Optional[str] = None,
) -> bool:
    """
    Paddle webhook signature'ını doğrular.

    Paddle her webhook'ta `Paddle-Signature` header'ı gönderir, format:
        ts=1234567890;h1=hash_value

    Doğrulama:
      1. Header'dan ts ve h1 ayır
      2. `{ts}:{raw_body}` formatında payload oluştur
      3. HMAC-SHA256 ile webhook secret kullanarak hash hesapla
      4. h1 ile karşılaştır (constant-time comparison)
      5. Timestamp 5 dakika içinde mi kontrol et (replay attack önlemi)

    Args:
        raw_body: Webhook'un raw HTTP body'si (bytes)
        signature_header: `Paddle-Signature` header değeri
        secret: Webhook signing secret (None ise env'den okunur)

    Returns:
        True if valid, False otherwise.

    Raises:
        PaddleSignatureError: Signature missing veya format hatalı.
    """
    if secret is None:
        secret = PADDLE_WEBHOOK_SECRET

    if not secret:
        raise PaddleSignatureError(
            "PADDLE_WEBHOOK_SECRET env değişkeni boş. "
            "Paddle dashboard'dan webhook secret'ı alıp env'e ekle."
        )

    if not signature_header:
        raise PaddleSignatureError("Paddle-Signature header eksik.")

    # Header'ı parse et
    try:
        parts = dict(part.split("=", 1) for part in signature_header.split(";"))
        ts = parts.get("ts")
        h1 = parts.get("h1")
    except ValueError:
        raise PaddleSignatureError(f"Geçersiz signature format: {signature_header}")

    if not ts or not h1:
        raise PaddleSignatureError(f"Signature eksik bileşen (ts veya h1): {signature_header}")

    # Timestamp kontrolü (replay attack önlemi)
    try:
        ts_int = int(ts)
    except ValueError:
        raise PaddleSignatureError(f"Geçersiz timestamp: {ts}")

    now = int(datetime.utcnow().timestamp())
    if abs(now - ts_int) > WEBHOOK_TIMESTAMP_TOLERANCE:
        logger.warning(
            f"Webhook timestamp tolerance dışında: ts={ts_int}, now={now}, "
            f"diff={now - ts_int}s"
        )
        return False

    # HMAC hesapla: payload = ts:raw_body
    signed_payload = f"{ts}:{raw_body.decode('utf-8')}".encode("utf-8")
    expected_h1 = hmac.new(
        secret.encode("utf-8"),
        signed_payload,
        hashlib.sha256,
    ).hexdigest()

    # Constant-time karşılaştırma
    return hmac.compare_digest(expected_h1, h1)


# ============================================
# PADDLE API CLIENT (async)
# ============================================

class PaddleClient:
    """
    Async Paddle Billing API client.

    Kullanım:
        async with PaddleClient() as client:
            tx = await client.create_transaction(...)
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or PADDLE_API_KEY
        if not self.api_key:
            raise PaddleError(
                "PADDLE_API_KEY env değişkeni boş. "
                "Paddle dashboard → Authentication → API keys'ten al."
            )
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        self._client = httpx.AsyncClient(
            base_url=PADDLE_API_BASE,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Paddle-Version": "1",
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
            raise PaddleError("PaddleClient context manager dışında kullanıldı.")

        response = await self._client.request(method, path, **kwargs)

        if response.status_code >= 400:
            body = {}
            try:
                body = response.json()
            except Exception:
                pass
            raise PaddleAPIError(
                response.status_code,
                body.get("error", {}).get("detail", response.text),
                body,
            )

        return response.json()

    # ========================================
    # CUSTOMERS
    # ========================================

    async def create_customer(self, email: str, name: Optional[str] = None) -> dict:
        """Yeni Paddle customer oluştur."""
        payload = {"email": email}
        if name:
            payload["name"] = name
        return await self._request("POST", "/customers", json=payload)

    async def get_or_create_customer(self, email: str, name: Optional[str] = None) -> dict:
        """
        Email'e göre customer bul, yoksa yarat.

        Paddle aynı email ile 2 customer oluşturmana izin vermiyor (409 döner),
        bu yüzden önce listeleyip kontrol ediyoruz.
        """
        # Email ile filtrele
        result = await self._request("GET", "/customers", params={"email": email})
        customers = result.get("data", [])
        if customers:
            return customers[0]

        # Yoksa yarat
        result = await self.create_customer(email, name)
        return result.get("data", {})

    # ========================================
    # TRANSACTIONS (checkout için)
    # ========================================

    async def create_transaction(
        self,
        price_id: str,
        customer_id: str,
        custom_data: Optional[dict] = None,
        quantity: int = 1,
    ) -> dict:
        """
        Checkout için transaction oluştur.

        Frontend bunu Paddle.Checkout.open({ transactionId }) ile açar.

        Args:
            price_id: Paddle price ID (pri_xxx)
            customer_id: Paddle customer ID (ctm_xxx)
            custom_data: Webhook'ta geri gelecek metadata (örn. {"user_id": 123, "plan_slug": "pro"})
            quantity: Item adedi (default 1)
        """
        payload = {
            "items": [
                {
                    "price_id": price_id,
                    "quantity": quantity,
                }
            ],
            "customer_id": customer_id,
            "collection_mode": "automatic",
        }
        if custom_data:
            payload["custom_data"] = custom_data

        result = await self._request("POST", "/transactions", json=payload)
        return result.get("data", {})

    async def get_transaction(self, transaction_id: str) -> dict:
        """Transaction detaylarını getir."""
        result = await self._request("GET", f"/transactions/{transaction_id}")
        return result.get("data", {})

    # ========================================
    # SUBSCRIPTIONS
    # ========================================

    async def get_subscription(self, subscription_id: str) -> dict:
        """Subscription detayı."""
        result = await self._request("GET", f"/subscriptions/{subscription_id}")
        return result.get("data", {})

    async def cancel_subscription(
        self,
        subscription_id: str,
        effective_from: str = "next_billing_period",
    ) -> dict:
        """
        Subscription iptal et.

        Args:
            effective_from: 'next_billing_period' (dönem sonu) veya 'immediately'
        """
        payload = {"effective_from": effective_from}
        result = await self._request(
            "POST",
            f"/subscriptions/{subscription_id}/cancel",
            json=payload,
        )
        return result.get("data", {})

    # ========================================
    # CUSTOMER PORTAL
    # ========================================

    async def create_portal_session(self, customer_id: str) -> dict:
        """
        Customer portal session URL'i oluştur.

        Kullanıcı 'Manage subscription' butonuna basınca buradaki URL'e
        yönlendirilir, orada subscription'ını yönetir.
        """
        result = await self._request(
            "POST",
            f"/customers/{customer_id}/portal-sessions",
        )
        return result.get("data", {})
