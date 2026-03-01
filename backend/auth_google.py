# backend/app/api/routes/auth_google.py
"""
Google OAuth Authentication Endpoint
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from google.oauth2 import id_token
from google.auth.transport import requests
from sqlalchemy.orm import Session
from datetime import datetime
import os

from ...database import get_db
from ...models.user import User
from ...services.auth_service import AuthService
from ...services.credit_service import CreditService

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Google Client ID - .env dosyasından alınacak
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

class GoogleAuthRequest(BaseModel):
    credential: str  # Google'dan gelen JWT token

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

@router.post("/google", response_model=AuthResponse)
async def google_auth(request: GoogleAuthRequest, db: Session = Depends(get_db)):
    """
    Google OAuth ile giriş/kayıt
    - Token'ı doğrula
    - Kullanıcı varsa: giriş yap
    - Kullanıcı yoksa: otomatik kayıt et
    """
    try:
        # Google token'ını doğrula
        idinfo = id_token.verify_oauth2_token(
            request.credential,
            requests.Request(),
            GOOGLE_CLIENT_ID
        )
        
        # Token bilgilerini al
        google_id = idinfo['sub']
        email = idinfo['email']
        name = idinfo.get('name', email.split('@')[0])
        picture = idinfo.get('picture', None)
        email_verified = idinfo.get('email_verified', False)
        
        if not email_verified:
            raise HTTPException(status_code=400, detail="Email not verified by Google")
        
        # Kullanıcıyı bul veya oluştur
        user = db.query(User).filter(User.email == email).first()
        
        if user:
            # Mevcut kullanıcı - Google ID'yi güncelle (eğer yoksa)
            if not user.google_id:
                user.google_id = google_id
                user.profile_picture = picture
                db.commit()
        else:
            # Yeni kullanıcı - otomatik kayıt
            user = User(
                email=email,
                name=name,
                google_id=google_id,
                profile_picture=picture,
                password_hash=None,  # Google ile giriş yapanlar için şifre yok
                is_active=True,
                created_at=datetime.utcnow()
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            
            # Yeni kullanıcıya başlangıç kredisi ver
            credit_service = CreditService(db)
            credit_service.initialize_user_credits(user.id)
        
        # JWT token oluştur
        auth_service = AuthService(db)
        access_token = auth_service.create_access_token(user.id)
        
        return AuthResponse(
            access_token=access_token,
            user={
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "profile_picture": user.profile_picture,
                "auth_provider": "google" if user.google_id else "email"
            }
        )
        
    except ValueError as e:
        # Token doğrulama hatası
        raise HTTPException(status_code=401, detail=f"Invalid Google token: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")
