"""
SimuTarget: DB Plan Düzeltme Script'i
Kullanım: python fix_plans.py
Proje kök dizininde çalıştır (src/ klasörünün bulunduğu yer)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from src.database.connection import engine

def fix_plans():
    with engine.connect() as conn:
        # Mevcut planları göster
        result = conn.execute(text("SELECT id, name, slug, price_monthly, credits_monthly FROM plans ORDER BY price_monthly"))
        print("\n=== MEVCUT PLANLAR ===")
        for row in result:
            print(f"  ID:{row[0]} | {row[1]:15s} | slug:{row[2]:12s} | ${row[3]:.2f} | {row[4]} kredi")
        
        # Basic → Starter güncelle
        updated = conn.execute(text("""
            UPDATE plans 
            SET name = 'Starter', slug = 'starter', price_monthly = 29.00, credits_monthly = 500
            WHERE slug = 'basic'
        """))
        if updated.rowcount > 0:
            print(f"\n✅ 'Basic' → 'Starter' olarak güncellendi ({updated.rowcount} satır)")
        
        # Disposable yoksa ekle
        exists = conn.execute(text("SELECT 1 FROM plans WHERE slug = 'disposable'")).fetchone()
        if not exists:
            conn.execute(text("""
                INSERT INTO plans (name, slug, price_monthly, credits_monthly, max_team_size, is_active, features)
                VALUES ('Disposable', 'disposable', 4.99, 50, 1, true, 
                '{"tests": {"single": true, "ab_compare": false, "multi_compare": false}, "reports": {"screen": true, "pdf": false, "dashboard": false, "custom": false}, "filters": {"age_range": false, "income_level": false, "education": false, "occupation": false, "marital_status": false, "big_five": false, "price_sensitivity": false}, "api_access": false, "max_personas_per_query": 50}'::jsonb)
            """))
            print("✅ 'Disposable' planı eklendi")
        else:
            print("ℹ️  'Disposable' planı zaten var")
        
        # Mevcut basic abonelikleri starter'a güncelle
        sub_updated = conn.execute(text("""
            UPDATE subscriptions s
            SET plan_id = (SELECT id FROM plans WHERE slug = 'starter')
            WHERE plan_id IN (SELECT id FROM plans WHERE slug = 'basic' OR name = 'Basic')
            AND status = 'active'
        """))
        if sub_updated.rowcount > 0:
            print(f"✅ {sub_updated.rowcount} aktif abonelik Basic → Starter'a güncellendi")
        
        conn.commit()
        
        # Sonuç
        result = conn.execute(text("SELECT id, name, slug, price_monthly, credits_monthly FROM plans WHERE is_active = true ORDER BY price_monthly"))
        print("\n=== GÜNCEL PLANLAR ===")
        for row in result:
            print(f"  ID:{row[0]} | {row[1]:15s} | slug:{row[2]:12s} | ${row[3]:.2f} | {row[4]} kredi")
        print()

if __name__ == "__main__":
    fix_plans()
