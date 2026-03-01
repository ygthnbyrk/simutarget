# backend/app/models/user.py - Google OAuth için güncellenmiş model
"""
User Model - Google OAuth desteği ile
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float
from sqlalchemy.sql import func
from ..database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=True)
    password_hash = Column(String(255), nullable=True)  # NULL for Google-only users
    
    # Google OAuth fields
    google_id = Column(String(255), unique=True, nullable=True, index=True)
    profile_picture = Column(String(500), nullable=True)
    
    # Account status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<User {self.email}>"
    
    @property
    def auth_provider(self):
        """Kullanıcının giriş yöntemini döndür"""
        if self.google_id and not self.password_hash:
            return "google"
        elif self.google_id and self.password_hash:
            return "both"
        else:
            return "email"
