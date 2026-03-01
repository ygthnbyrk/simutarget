"""Kredi sistemi testi"""
from datetime import datetime, timedelta
from src.database.connection import SessionLocal
from src.database.models import User, Plan, Subscription, CreditLedger
from src.database.credit_service import CreditService, FeatureGateService
from passlib.hash import bcrypt

db = SessionLocal()

print("=" * 50)
print("SimuTarget Kredi Sistemi Testi")
print("=" * 50)

# 1. Test kullanıcısı oluştur
print("\n1️⃣ Test kullanıcısı oluşturuluyor...")
test_user = db.query(User).filter(User.email == "test@simutarget.ai").first()
if not test_user:
    test_user = User(
        email="test@simutarget.ai",
        name="Test Kullanıcı",
        password_hash=bcrypt.hash("test123"),
        role="user"
    )
    db.add(test_user)
    db.commit()
    db.refresh(test_user)
print(f"   ✅ Kullanıcı: {test_user.name} (ID: {test_user.id})")

# 2. Pro plana abone et
print("\n2️⃣ Pro plana abone ediliyor...")
pro_plan = db.query(Plan).filter(Plan.slug == "pro").first()
print(f"   Plan: {pro_plan.name} - ${pro_plan.price_monthly}/ay - {pro_plan.credits_monthly} kredi")

subscription = db.query(Subscription).filter(Subscription.user_id == test_user.id).first()
if not subscription:
    subscription = Subscription(
        user_id=test_user.id,
        plan_id=pro_plan.id,
        status="active",
        current_period_start=datetime.utcnow(),
        current_period_end=datetime.utcnow() + timedelta(days=30),
    )
    db.add(subscription)
    db.commit()
print(f"   ✅ Abonelik aktif, bitiş: {subscription.current_period_end.strftime('%d/%m/%Y')}")

# 3. Kredi yükle
print("\n3️⃣ Kredi yükleniyor...")
credit_service = CreditService(db)
credit_service.grant_credits(
    user_id=test_user.id,
    amount=pro_plan.credits_monthly,
    description="Aylık Pro kredisi",
    expires_at=subscription.current_period_end
)
balance = credit_service.get_balance(test_user.id)
print(f"   ✅ Bakiye: {balance} kredi")

# 4. Kampanya simülasyonu - 30 persona sorgusu
print("\n4️⃣ Kampanya simülasyonu (30 persona)...")
result = credit_service.check_and_reserve(
    user_id=test_user.id,
    amount=30,
    reference_id="campaign_test_001"
)
print(f"   Rezervasyon: {result['message']}")
print(f"   Kalan bakiye: {result['balance']}")

# 5. Sorgu başarılı - kullanımı onayla
print("\n5️⃣ Kullanım onaylanıyor...")
credit_service.confirm_usage(
    user_id=test_user.id,
    amount=30,
    reference_id="campaign_test_001"
)
balance = credit_service.get_balance(test_user.id)
print(f"   ✅ Onaylandı. Kalan bakiye: {balance}")

# 6. İkinci kampanya - 50 persona
print("\n6️⃣ İkinci kampanya (50 persona)...")
result2 = credit_service.check_and_reserve(
    user_id=test_user.id,
    amount=50,
    reference_id="campaign_test_002"
)
print(f"   Rezervasyon: {result2['message']}")
print(f"   Kalan bakiye: {result2['balance']}")

# 7. Bu sorgu başarısız oldu - krediyi geri ver
print("\n7️⃣ Sorgu başarısız! Kredi iade ediliyor...")
credit_service.release_reserve(
    user_id=test_user.id,
    amount=50,
    reference_id="campaign_test_002"
)
balance = credit_service.get_balance(test_user.id)
print(f"   ✅ İade edildi. Kalan bakiye: {balance}")

# 8. Yetersiz kredi testi
print("\n8️⃣ Yetersiz kredi testi (200 persona)...")
result3 = credit_service.check_and_reserve(
    user_id=test_user.id,
    amount=200,
    reference_id="campaign_test_003"
)
print(f"   ❌ {result3['message']}")

# 9. Feature gate testi
print("\n9️⃣ Feature gate testi...")
gate_service = FeatureGateService(db)

# Pro kullanıcı yaş filtresine erişebilir mi?
age_check = gate_service.check_filter_access(test_user.id, "age_range")
print(f"   Yaş filtresi: {'✅ Erişim var' if age_check['allowed'] else '❌ ' + age_check['message']}")

# Pro kullanıcı eğitim filtresine erişebilir mi?
edu_check = gate_service.check_filter_access(test_user.id, "education")
print(f"   Eğitim filtresi: {'✅ Erişim var' if edu_check['allowed'] else '❌ ' + edu_check['message'] + ' → ' + edu_check.get('upgrade_to', '')}")

# Pro kullanıcı A/B test yapabilir mi?
ab_check = gate_service.check_test_type_access(test_user.id, "ab_compare")
print(f"   A/B Test: {'✅ Erişim var' if ab_check['allowed'] else '❌ ' + ab_check['message']}")

# Pro kullanıcı dashboard görebilir mi?
dash_check = gate_service.check_report_access(test_user.id, "dashboard")
print(f"   Dashboard: {'✅ Erişim var' if dash_check['allowed'] else '❌ ' + dash_check['message'] + ' → ' + dash_check.get('upgrade_to', '')}")

# 10. Kullanım özeti
print("\n🔟 Kullanım özeti...")
summary = credit_service.get_usage_summary(test_user.id)
print(f"   Bakiye: {summary['current_balance']}")
print(f"   Toplam yüklenen: {summary['total_granted']}")
print(f"   Toplam kullanılan: {summary['total_used']}")
print(f"   Kullanım oranı: %{summary['usage_percentage']}")

print("\n" + "=" * 50)
print("✅ TÜM TESTLER TAMAMLANDI!")
print("=" * 50)

db.close()