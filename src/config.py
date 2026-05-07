"""Application configuration."""

import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_env: str = "development"
    debug: bool = True
    log_level: str = "INFO"
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    
    # Database
    database_url: str = "postgresql://simutarget:simutarget@localhost:5432/simutarget"
    
    # Qdrant
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333

    # Paddle Billing (oturum #7.8) — DEPRECATED, LS canlıya geçtikten sonra silinecek
    paddle_api_key: str = ""
    paddle_webhook_secret: str = ""
    paddle_environment: str = "production"  # production | sandbox

    # Lemon Squeezy (oturum #7.9) — ACTIVE provider
    lemonsqueezy_api_key: str = ""
    lemonsqueezy_store_id: str = ""
    lemonsqueezy_webhook_secret: str = ""

    # Hangi payment provider aktif: "lemonsqueezy" | "paddle"
    # Şu an dokümantasyon amaçlı; ileride frontend hangi JS SDK'yı yükleyeceğini
    # bu değere göre seçer (Lemon.js vs Paddle.js).
    payment_provider: str = "lemonsqueezy"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
