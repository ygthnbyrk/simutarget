"""
Plan features'a media (görsel/video) erişim bilgisi ekle.

Kullanım:
  cd simutarget
  python -m src.migrations.add_media_features

Veya doğrudan PowerShell'den:
  python add_media_features.py

Tier erişim matrisi:
  - Basic ($4.99):      image=False, video=False
  - Pro ($9.99):        image=True,  video=False
  - Business ($19.99):  image=True,  video=True
  - Enterprise ($49.99): image=True,  video=True
"""

import os
import sys

# Proje kök dizinini path'e ekle
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# .env'den DATABASE_URL al
from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/simutarget")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

# ============================================
# MEDIA FEATURE MATRİSİ
# ============================================

MEDIA_FEATURES = {
    "basic": {"image": False, "video": False},
    "pro": {"image": True, "video": False},
    "business": {"image": True, "video": True},
    "enterprise": {"image": True, "video": True},
}


def update_plan_features():
    """Mevcut planların features JSON'ına media alanı ekle."""
    from src.database.models import Plan
    
    plans = db.query(Plan).all()
    
    if not plans:
        print("❌ Hiç plan bulunamadı! Önce seed data'yı çalıştırın.")
        return
    
    updated = 0
    for plan in plans:
        slug = plan.slug.lower()
        media_config = MEDIA_FEATURES.get(slug)
        
        if not media_config:
            print(f"⚠️  {plan.name} ({plan.slug}) için media config bulunamadı, atlanıyor.")
            continue
        
        # Mevcut features'ı güncelle
        features = plan.features or {}
        
        if features.get("media") == media_config:
            print(f"✓  {plan.name} — zaten güncel")
            continue
        
        features["media"] = media_config
        plan.features = features
        
        # SQLAlchemy JSON değişikliğini algılasın
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(plan, "features")
        
        print(f"✅ {plan.name} ({plan.slug}) → media: {media_config}")
        updated += 1
    
    if updated > 0:
        db.commit()
        print(f"\n🎉 {updated} plan güncellendi!")
    else:
        print("\n✓ Tüm planlar zaten güncel.")
    
    # Doğrulama
    print("\n📋 Güncel Plan Features (media):")
    print("-" * 50)
    for plan in db.query(Plan).order_by(Plan.price_monthly).all():
        media = plan.features.get("media", {})
        print(f"  {plan.name:15s} ${plan.price_monthly:>6} → image={media.get('image', '?')}, video={media.get('video', '?')}")


if __name__ == "__main__":
    print("🔄 SimuTarget — Plan Media Features Migration")
    print("=" * 50)
    update_plan_features()
    db.close()
    print("\n✅ Tamamlandı!")
