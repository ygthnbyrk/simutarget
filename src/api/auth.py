"""SimuTarget Kimlik Doğrulama Sistemi"""
import hashlib
import logging
import os
import re
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
import bcrypt as _bcrypt
import httpx
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from src.database.connection import get_db
from src.database.models import User, Subscription, Plan, PasswordResetToken
from src.database.credit_service import CreditService
from src.services.notification_service import notify_new_user
from src.services.email_service import send_password_reset_email
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# JWT Ayarları
# Güvensiz bir default'a asla düşülmez: SECRET_KEY env'de tanımlı değilse
# uygulama başlarken hemen patlar (production'da sessizce zayıf bir anahtarla
# imzalamaktansa çökmek daha güvenli).
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY ortam değişkeni tanımlı değil. JWT imzalamak için "
        "gerekli — .env dosyasına (veya deploy ortamındaki env ayarlarına) "
        "rastgele, güçlü bir SECRET_KEY ekleyin. Örnek üretmek için: "
        "python -c \"import secrets; print(secrets.token_urlsafe(48))\""
    )
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 saat

# Google OAuth Ayarları (oturum #8.1)
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")

# Şifre sıfırlama (oturum #8.3)
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://simutarget.ai")
PASSWORD_RESET_EXPIRE_HOURS = 1
MIN_PASSWORD_LENGTH = 8

# Cloudflare Turnstile (oturum #9.0 — bot koruması)
TURNSTILE_SECRET_KEY = os.getenv("TURNSTILE_SECRET_KEY", "")
TURNSTILE_VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"

security = HTTPBearer()


# ---- Pydantic Modelleri ----

class UserRegister(BaseModel):
    email: str
    name: str
    password: str
    # Cloudflare Turnstile token (oturum #9.0)
    turnstile_token: Optional[str] = None
    # Honeypot — gerçek kullanıcı boş bırakır, bot doldurur. Doluysa kayıt reddedilir.
    website: Optional[str] = ""

class UserLogin(BaseModel):
    email: str
    password: str
    turnstile_token: Optional[str] = None

class GoogleLoginRequest(BaseModel):
    """Frontend'den gelen Google ID token (credential)."""
    credential: str

class ForgotPasswordRequest(BaseModel):
    """Şifre sıfırlama talebi — kullanıcı email'ini girer."""
    email: str
    turnstile_token: Optional[str] = None

class ResetPasswordRequest(BaseModel):
    """Şifre sıfırlama tamamlama — email'deki token + yeni şifre."""
    token: str
    new_password: str

class MessageResponse(BaseModel):
    message: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

class UserProfile(BaseModel):
    id: int
    email: str
    name: str
    role: str
    plan: Optional[dict] = None
    credits: Optional[dict] = None


# ---- Yardımcı Fonksiyonlar ----

def create_access_token(data: dict) -> str:
    """JWT token oluştur"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_password(password: str, hashed: str) -> bool:
    return _bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


def hash_password(password: str) -> str:
    return _bcrypt.hashpw(password.encode("utf-8"), _bcrypt.gensalt()).decode("utf-8")


def _hash_reset_token(raw_token: str) -> str:
    """Ham reset token'ın SHA256 hex'i — DB'ye yalnızca bu yazılır."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


# ---- Bot Koruması (oturum #9.0) ----

def verify_turnstile_token(token: Optional[str]) -> bool:
    """
    Cloudflare Turnstile token doğrulaması (siteverify).

    Davranış:
      - TURNSTILE_SECRET_KEY tanımlı DEĞİLSE: özellik kapalı kabul edilir ve
        doğrulama atlanır (fail-open). Böylece env var unutulursa tüm kayıt/giriş
        akışı kilitlenmez — bot koruması düşer ama servis ayakta kalır.
      - Secret tanımlıysa ve token boş/yoksa: başarısız (fail-closed).
      - Secret tanımlıysa: Cloudflare'e sorulur; success=false ise başarısız.
      - Cloudflare'e ağ hatası olursa: uyarı loglanır, fail-open (Cloudflare
        kesintisinde meşru kullanıcılar engellenmesin). Token geçersizse zaten
        success=false döner ve fail-closed olur; ağ hatasını bot tetikleyemez.
    """
    if not TURNSTILE_SECRET_KEY:
        return True  # özellik yapılandırılmamış — doğrulamayı atla

    if not token:
        return False

    try:
        resp = httpx.post(
            TURNSTILE_VERIFY_URL,
            data={"secret": TURNSTILE_SECRET_KEY, "response": token},
            timeout=5.0,
        )
        result = resp.json()
        success = bool(result.get("success"))
        if not success:
            logger.info(f"Turnstile doğrulama başarısız: {result.get('error-codes')}")
        return success
    except Exception as e:
        logger.warning(f"Turnstile siteverify çağrısı başarısız (fail-open): {e}")
        return True


# İsimde reddedilecek desenler: URL/link/promosyon/injection işaretleri
_NAME_BANNED_PATTERNS = re.compile(
    r"(https?://|www\.|\.com|\.net|\.org|\.ru|\.xyz|\.io|bit\.ly|t\.me|telegram|@|<|>)",
    re.IGNORECASE,
)


def _validate_name(name: str) -> str:
    """
    Kayıt sırasında isim alanı doğrulaması (oturum #9.0 — spam koruması).

    Bahis/casino botları isim alanına link/promosyon metni basıyor
    ("50.000 TL bonus + 250 spin ... bit.ly/..."). Bu fonksiyon onları reddeder.
    Temizlenmiş ismi döner; geçersizse HTTP 400 fırlatır.
    """
    cleaned = (name or "").strip()

    if len(cleaned) < 2 or len(cleaned) > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="İsim 2-50 karakter arasında olmalıdır."
        )

    # URL / link / promosyon / injection içeriği reddi
    if _NAME_BANNED_PATTERNS.search(cleaned):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="İsim geçersiz karakterler içeriyor."
        )

    # Kontrol karakterleri / yeni satır reddi
    if any(ord(ch) < 32 for ch in cleaned):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="İsim geçersiz karakterler içeriyor."
        )

    # İsimler ağırlıkla harf+boşluk olmalı; aşırı rakam/sembol/emoji reddi
    letters = sum(ch.isalpha() or ch.isspace() for ch in cleaned)
    if letters / max(len(cleaned), 1) < 0.5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="İsim geçersiz görünüyor."
        )

    return cleaned


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """JWT token'dan kullanıcıyı çıkar — FastAPI dependency"""
    token = credentials.credentials
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Geçersiz veya süresi dolmuş token.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not user.is_active:
        raise credentials_exception

    return user


def get_current_admin(
    user: User = Depends(get_current_user)
) -> User:
    """
    Admin yetkisi gerektiren endpoint'ler için dependency.

    User.role == "admin" değilse 403 döner.
    Kendi user'ını admin yapmak için (production DB'de):
        UPDATE users SET role = 'admin' WHERE email = 'senin@email.com';
    """
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için admin yetkisi gerekli."
        )
    return user


# ---- Auth Endpoint Fonksiyonları ----

def register_user(data: UserRegister, db: Session) -> TokenResponse:
    """Yeni kullanıcı kaydı"""
    # --- Bot koruması (oturum #9.0): honeypot → Turnstile → isim validasyonu ---
    # 1. Honeypot: gerçek kullanıcı bu alanı görmez/boş bırakır; doluysa bot.
    if data.website:
        logger.info("Register honeypot tetiklendi — istek reddedildi.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Geçersiz kayıt isteği."
        )

    # 2. Turnstile doğrulaması
    if not verify_turnstile_token(data.turnstile_token):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Doğrulama başarısız. Lütfen sayfayı yenileyip tekrar deneyin."
        )

    # 3. İsim validasyonu (spam/link reddi) — temizlenmiş ismi döner
    clean_name = _validate_name(data.name)

    # Email kontrolü
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu email adresi zaten kayıtlı."
        )

    # Kullanıcı oluştur
    user = User(
        email=data.email,
        name=clean_name,
        password_hash=hash_password(data.password),
        role="user",
        auth_provider="email",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Token oluştur
    token = create_access_token({"sub": str(user.id)})

    # Telegram bildirimi (fire-and-forget — hata olursa register etkilenmez)
    try:
        total_users = db.query(User).count()
        notify_new_user(
            email=user.email,
            user_id=user.id,
            name=user.name,
            total_users=total_users,
        )
    except Exception as e:
        # Bildirim hatası register'ı bozmasın
        logger.warning(f"Yeni üye bildirimi gönderilemedi: {e}")

    return TokenResponse(
        access_token=token,
        user={"id": user.id, "email": user.email, "name": user.name}
    )


def login_user(data: UserLogin, db: Session) -> TokenResponse:
    """Kullanıcı girişi"""
    # Bot koruması (oturum #9.0): Turnstile doğrulaması
    if not verify_turnstile_token(data.turnstile_token):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Doğrulama başarısız. Lütfen sayfayı yenileyip tekrar deneyin."
        )

    user = db.query(User).filter(User.email == data.email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email veya şifre hatalı."
        )

    # Google ile kayıt olmuş kullanıcı şifreyle giriş yapmaya çalışıyorsa
    if not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bu hesap Google ile kayıtlı. Lütfen Google ile giriş yapın."
        )

    if not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email veya şifre hatalı."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hesabınız devre dışı."
        )

    token = create_access_token({"sub": str(user.id)})

    return TokenResponse(
        access_token=token,
        user={"id": user.id, "email": user.email, "name": user.name}
    )


def login_or_register_google(data: GoogleLoginRequest, db: Session) -> TokenResponse:
    """
    Google OAuth ile giriş veya kayıt.

    Frontend'den gelen ID token'ı Google'a verify ettirir, kullanıcıyı bulur
    veya yenisini oluşturur. Tek kullanıcı tek user row mantığı:
      - Email mevcutsa: o user'a Google'ı bağla (auto-link)
      - Email yoksa: yeni user oluştur, Telegram bildirimi gönder

    Frontend → POST /api/v1/auth/google {"credential": "<id_token>"}

    Not (oturum #9.0): Bu akışa Turnstile EKLENMEDİ — Google ID token zaten
    bot tarafından forge edilemez, ek doğrulama gereksiz sürtünme yaratır.
    """
    if not GOOGLE_CLIENT_ID:
        logger.error("GOOGLE_CLIENT_ID env var tanımlı değil!")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth backend'de yapılandırılmamış."
        )

    # 1. Google ID token'ı verify et
    try:
        from google.oauth2 import id_token
        from google.auth.transport import requests as google_requests

        idinfo = id_token.verify_oauth2_token(
            data.credential,
            google_requests.Request(),
            GOOGLE_CLIENT_ID,
            clock_skew_in_seconds=10,  # küçük zaman farkları için tolerans
        )
    except ValueError as e:
        logger.warning(f"Google token verify başarısız: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google kimlik doğrulama başarısız. Lütfen tekrar deneyin."
        )
    except ImportError:
        logger.error("google-auth paketi yüklü değil!")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Backend Google OAuth için yapılandırılmamış."
        )
    except Exception as e:
        logger.error(f"Google token verify beklenmedik hata: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google kimlik doğrulama başarısız."
        )

    # 2. Google'dan gelen bilgileri çıkar
    google_id = idinfo.get("sub")  # Google'ın unique user ID'si
    email = idinfo.get("email", "").lower().strip()
    email_verified = idinfo.get("email_verified", False)
    name = idinfo.get("name") or email.split("@")[0]

    if not google_id or not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google hesabından email veya ID alınamadı."
        )

    if not email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Google hesabınızın email adresi doğrulanmamış."
        )

    # 3. Kullanıcı arama — önce google_id, sonra email
    user = db.query(User).filter(User.google_id == google_id).first()

    is_new_user = False

    if not user:
        # Aynı email mevcut mu? (email/password ile kayıt olmuş olabilir)
        user = db.query(User).filter(User.email == email).first()

        if user:
            # MEVCUT EMAIL — Google hesabını otomatik bağla
            user.google_id = google_id
            if user.auth_provider == "email":
                # auth_provider'ı "email" olarak bırakırız — birden fazla yöntem var
                # ama UI için ilk kayıt yöntemi önemli; istersen "both" yapılabilir
                pass
            db.commit()
            db.refresh(user)
        else:
            # YENİ KULLANICI — kayıt oluştur
            user = User(
                email=email,
                name=name[:100],
                password_hash=None,  # Google ile geldi, şifre yok
                role="user",
                google_id=google_id,
                auth_provider="google",
                is_active=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            is_new_user = True

    # 4. Hesap aktif mi?
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hesabınız devre dışı."
        )

    # 5. JWT token oluştur
    token = create_access_token({"sub": str(user.id)})

    # 6. Yeni user ise Telegram bildirimi (fire-and-forget)
    if is_new_user:
        try:
            total_users = db.query(User).count()
            notify_new_user(
                email=user.email,
                user_id=user.id,
                name=user.name,
                total_users=total_users,
            )
        except Exception as e:
            logger.warning(f"Yeni üye bildirimi gönderilemedi: {e}")

    return TokenResponse(
        access_token=token,
        user={"id": user.id, "email": user.email, "name": user.name}
    )


def forgot_password(data: ForgotPasswordRequest, db: Session) -> MessageResponse:
    """
    Şifre sıfırlama talebi (oturum #8.3).

    Güvenlik:
      - Email var/yok bilgisini SIZDIRMAZ (enumeration koruması): her durumda
        aynı generic 200 döner.
      - Ham token yalnızca email'e gider; DB'ye yalnızca SHA256 hash yazılır.
      - 1 saat geçerli, tek kullanımlık.
      - Yeni token üretilince kullanıcının eski kullanılmamış token'ları
        geçersiz kılınır (used=True).
      - Google-only kullanıcılar da sıfırlayabilir (şifre belirleyip email
        girişi ekleyebilir); google_id korunur.
      - (oturum #9.0) Turnstile doğrulaması en başta — reset-spam koruması.
        Bu kontrol email enumeration sızdırmaz (botu eler, email varlığını açmaz).
    """
    # Bot koruması (oturum #9.0): Turnstile doğrulaması
    if not verify_turnstile_token(data.turnstile_token):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Doğrulama başarısız. Lütfen sayfayı yenileyip tekrar deneyin."
        )

    generic = MessageResponse(
        message="Eğer bu email adresi kayıtlıysa, şifre sıfırlama bağlantısı gönderildi."
    )

    email = (data.email or "").lower().strip()
    if not email:
        return generic

    user = db.query(User).filter(User.email == email).first()
    if not user or not user.is_active:
        return generic

    # Eski kullanılmamış token'ları geçersiz kıl
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.used == False,  # noqa: E712
    ).update({"used": True}, synchronize_session=False)

    # Yeni token üret — ham token email'e, hash DB'ye
    raw_token = secrets.token_urlsafe(32)
    reset_token = PasswordResetToken(
        user_id=user.id,
        token_hash=_hash_reset_token(raw_token),
        expires_at=datetime.utcnow() + timedelta(hours=PASSWORD_RESET_EXPIRE_HOURS),
        used=False,
    )
    db.add(reset_token)
    db.commit()

    # Email gönder (fire-and-forget — hata sıfırlama akışını bozmaz)
    reset_url = f"{FRONTEND_URL.rstrip('/')}/reset-password/{raw_token}"
    try:
        send_password_reset_email(
            to_email=user.email,
            name=user.name,
            reset_url=reset_url,
        )
    except Exception as e:
        logger.warning(f"Şifre sıfırlama emaili gönderilemedi: {e}")

    return generic


def reset_password(data: ResetPasswordRequest, db: Session) -> MessageResponse:
    """
    Şifre sıfırlama tamamlama (oturum #8.3).

    Email'deki ham token + yeni şifre alınır. Token'ın hash'i DB'de aranır,
    geçerliyse (kullanılmamış + süresi dolmamış) şifre güncellenir ve token
    kullanılmış işaretlenir.
    """
    if not data.token or not data.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token ve yeni şifre zorunludur."
        )

    if len(data.new_password) < MIN_PASSWORD_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Şifre en az {MIN_PASSWORD_LENGTH} karakter olmalıdır."
        )

    token_hash = _hash_reset_token(data.token)
    reset_token = (
        db.query(PasswordResetToken)
        .filter(PasswordResetToken.token_hash == token_hash)
        .first()
    )

    invalid_exc = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Geçersiz veya süresi dolmuş bağlantı. Lütfen yeni bir sıfırlama isteyin."
    )

    if not reset_token or reset_token.used or reset_token.expires_at <= datetime.utcnow():
        raise invalid_exc

    user = db.query(User).filter(User.id == reset_token.user_id).first()
    if not user or not user.is_active:
        raise invalid_exc

    # Şifreyi güncelle, token'ı kullanıldı işaretle
    user.password_hash = hash_password(data.new_password)
    reset_token.used = True
    db.commit()

    return MessageResponse(
        message="Şifreniz başarıyla güncellendi. Yeni şifrenizle giriş yapabilirsiniz."
    )


def get_user_profile(user: User, db: Session) -> UserProfile:
    """Kullanıcı profili ve kredi bilgisi"""
    # Aktif abonelik
    subscription = (
        db.query(Subscription)
        .filter(
            Subscription.user_id == user.id,
            Subscription.status == "active"
        )
        .first()
    )

    plan_info = None
    credits_info = None

    if subscription:
        plan = db.query(Plan).filter(Plan.id == subscription.plan_id).first()
        plan_info = {
            "name": plan.name,
            "slug": plan.slug,
            "price": float(plan.price_monthly),
            "period_end": subscription.current_period_end.isoformat()
        }

        credit_service = CreditService(db)
        credits_info = credit_service.get_usage_summary(user.id)

    return UserProfile(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        plan=plan_info,
        credits=credits_info
    )
