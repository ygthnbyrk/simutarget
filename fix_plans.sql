-- SimuTarget: DB Plan Düzeltme Script'i
-- Sorun: DB'de eski "Basic" plan hâlâ var, "Disposable" ve "Starter" yok
-- 
-- KULLANIM: psql ile veya pgAdmin'de çalıştır
-- ÖNEMLİ: Önce mevcut durumu kontrol et!

-- 1. Mevcut planları göster
SELECT id, name, slug, price_monthly, credits_monthly, is_active FROM plans ORDER BY price_monthly;

-- 2. Eğer "basic" slug'lı plan varsa → Starter'a güncelle
-- (Mevcut abonelikleri korumak için DELETE değil UPDATE yapıyoruz)
UPDATE plans 
SET name = 'Starter', 
    slug = 'starter', 
    price_monthly = 29.00, 
    credits_monthly = 500
WHERE slug = 'basic';

-- 3. Disposable planı yoksa ekle
INSERT INTO plans (name, slug, price_monthly, credits_monthly, max_team_size, is_active, features)
SELECT 'Disposable', 'disposable', 4.99, 50, 1, true, 
       '{"tests": {"single": true, "ab_compare": false, "multi_compare": false}, "reports": {"screen": true, "pdf": false, "dashboard": false, "custom": false}, "filters": {"age_range": false, "income_level": false, "education": false, "occupation": false, "marital_status": false, "big_five": false, "price_sensitivity": false}, "api_access": false, "max_personas_per_query": 50}'::jsonb
WHERE NOT EXISTS (SELECT 1 FROM plans WHERE slug = 'disposable');

-- 4. Doğrulama: 5 plan olmalı
SELECT id, name, slug, price_monthly, credits_monthly, is_active 
FROM plans 
WHERE is_active = true 
ORDER BY price_monthly;

-- Beklenen sonuç:
-- Disposable  | disposable  | 4.99   | 50
-- Starter     | starter     | 29.00  | 500
-- Pro         | pro         | 79.00  | 2000
-- Business    | business    | 199.00 | 5000
-- Enterprise  | enterprise  | 999.00 | 50000
