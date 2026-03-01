"""SimuTarget Kimlik Doğrulama Sistemi"""
import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
import bcrypt as _bcrypt
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from src.database.connection import get_db
from src.database.models import User, Subscription, Plan
from src.database.credit_service import CreditService
from dotenv import load_dotenv

load_dotenv()

# JWT Ayarları
SECRET_KEY = os.getenv("SECRET_KEY", "simutarget-secret-key-degistir-bunu")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 saat

security = HTTPBearer()


# ---- Pydantic Modelleri ----

class UserRegister(BaseModel):
    email: str
    name: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

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


# ---- Auth Endpoint Fonksiyonları ----

def register_user(data: UserRegister, db: Session) -> TokenResponse:
    """Yeni kullanıcı kaydı"""
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
        name=data.name,
        password_hash=hash_password(data.password),
        role="user"
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Token oluştur
    token = create_access_token({"sub": str(user.id)})

    return TokenResponse(
        access_token=token,
        user={"id": user.id, "email": user.email, "name": user.name}
    )


def login_user(data: UserLogin, db: Session) -> TokenResponse:
    """Kullanıcı girişi"""
    user = db.query(User).filter(User.email == data.email).first()
    
    if not user or not verify_password(data.password, user.password_hash):
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