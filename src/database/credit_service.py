"""SimuTarget Kredi Yönetim Servisi"""
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from src.database.models import CreditLedger, Subscription, Plan, User


class CreditService:
    """Kredi kontrolü, rezervasyon, harcama ve sıfırlama işlemleri"""

    def __init__(self, db: Session):
        self.db = db

    def get_balance(self, user_id: int) -> int:
        """Kullanıcının güncel kredi bakiyesini getir"""
        last_entry = (
            self.db.query(CreditLedger)
            .filter(CreditLedger.user_id == user_id)
            .order_by(CreditLedger.id.desc())
            .first()
        )
        return last_entry.balance_after if last_entry else 0

    def grant_credits(self, user_id: int, amount: int, description: str, expires_at: datetime = None) -> CreditLedger:
        """Kullanıcıya kredi yükle (abonelik yenilemesi, topup vb.)"""
        current_balance = self.get_balance(user_id)
        new_balance = current_balance + amount

        entry = CreditLedger(
            user_id=user_id,
            amount=amount,
            type="grant",
            balance_after=new_balance,
            description=description,
            expires_at=expires_at,
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def check_and_reserve(self, user_id: int, amount: int, reference_id: str) -> dict:
        """
        Kredi kontrolü yap ve yeterliyse rezerve et.
        Döndürür: {"success": True/False, "balance": int, "message": str}
        """
        current_balance = self.get_balance(user_id)

        if current_balance < amount:
            return {
                "success": False,
                "balance": current_balance,
                "message": f"Yetersiz kredi. Gerekli: {amount}, Mevcut: {current_balance}"
            }

        # Krediyi rezerve et (henüz harcamadık, tutuyoruz)
        new_balance = current_balance - amount
        entry = CreditLedger(
            user_id=user_id,
            amount=-amount,
            type="reserve",
            balance_after=new_balance,
            reference_id=reference_id,
            description=f"Rezerve: {reference_id}",
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)

        return {
            "success": True,
            "balance": new_balance,
            "message": f"{amount} kredi rezerve edildi.",
            "ledger_id": entry.id
        }

    def confirm_usage(self, user_id: int, amount: int, reference_id: str) -> CreditLedger:
        """
        Rezerve edilen krediyi kullanıma çevir.
        Sorgu başarıyla tamamlandığında çağrılır.
        """
        # Bakiye zaten reserve sırasında düşürüldü, sadece kayıt tutuyoruz
        current_balance = self.get_balance(user_id)

        entry = CreditLedger(
            user_id=user_id,
            amount=0,  # bakiye zaten düştü
            type="usage",
            balance_after=current_balance,
            reference_id=reference_id,
            description=f"Kullanım onaylandı: {reference_id}",
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def release_reserve(self, user_id: int, amount: int, reference_id: str) -> CreditLedger:
        """
        Rezervasyonu iptal et (sorgu başarısız olursa krediyi geri ver).
        """
        current_balance = self.get_balance(user_id)
        new_balance = current_balance + amount

        entry = CreditLedger(
            user_id=user_id,
            amount=amount,
            type="release",
            balance_after=new_balance,
            reference_id=reference_id,
            description=f"Rezerve iade: {reference_id}",
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def topup_credits(self, user_id: int, amount: int, expires_at: datetime = None) -> CreditLedger:
        """Ek kredi satın alma"""
        current_balance = self.get_balance(user_id)
        new_balance = current_balance + amount

        entry = CreditLedger(
            user_id=user_id,
            amount=amount,
            type="topup",
            balance_after=new_balance,
            description=f"Ek kredi satın alma: +{amount}",
            expires_at=expires_at,
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def expire_credits(self, user_id: int) -> CreditLedger:
        """Ay sonu kredi sıfırlama"""
        current_balance = self.get_balance(user_id)

        if current_balance <= 0:
            return None

        entry = CreditLedger(
            user_id=user_id,
            amount=-current_balance,
            type="expire",
            balance_after=0,
            description="Ay sonu kredi sıfırlama",
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def get_usage_summary(self, user_id: int) -> dict:
        """Kullanıcının kredi kullanım özeti"""
        total_granted = (
            self.db.query(func.sum(CreditLedger.amount))
            .filter(
                CreditLedger.user_id == user_id,
                CreditLedger.type.in_(["grant", "topup"])
            )
            .scalar() or 0
        )

        total_used = abs(
            self.db.query(func.sum(CreditLedger.amount))
            .filter(
                CreditLedger.user_id == user_id,
                CreditLedger.type == "reserve"
            )
            .scalar() or 0
        )

        current_balance = self.get_balance(user_id)

        return {
            "current_balance": current_balance,
            "total_granted": total_granted,
            "total_used": total_used,
            "usage_percentage": round((total_used / total_granted * 100), 1) if total_granted > 0 else 0
        }


class FeatureGateService:
    """Paket bazlı özellik erişim kontrolü"""

    def __init__(self, db: Session):
        self.db = db

    def get_user_plan(self, user_id: int) -> Plan:
        """Kullanıcının aktif planını getir"""
        subscription = (
            self.db.query(Subscription)
            .filter(
                Subscription.user_id == user_id,
                Subscription.status == "active",
                Subscription.current_period_end > datetime.utcnow()
            )
            .first()
        )
        if not subscription:
            return None
        return subscription.plan

    def check_filter_access(self, user_id: int, filter_name: str) -> dict:
        """Kullanıcının belirli bir filtreye erişimi var mı?"""
        plan = self.get_user_plan(user_id)

        if not plan:
            return {
                "allowed": False,
                "message": "Aktif abonelik bulunamadı.",
                "upgrade_to": "starter"
            }

        has_access = plan.has_feature("filters", filter_name)

        if has_access:
            return {"allowed": True, "message": "Erişim var."}

        # Hangi plana yükseltmesi gerektiğini bul
        upgrade_plan = self._find_upgrade_plan(filter_name)

        return {
            "allowed": False,
            "message": f"Bu filtre {plan.name} paketinde mevcut değil.",
            "upgrade_to": upgrade_plan
        }

    def check_test_type_access(self, user_id: int, test_type: str) -> dict:
        """Kullanıcının belirli bir test türüne erişimi var mı?"""
        plan = self.get_user_plan(user_id)

        if not plan:
            return {
                "allowed": False,
                "message": "Aktif abonelik bulunamadı.",
                "upgrade_to": "starter"
            }

        has_access = plan.has_feature("tests", test_type)

        if has_access:
            return {"allowed": True, "message": "Erişim var."}

        return {
            "allowed": False,
            "message": f"{test_type} testi {plan.name} paketinde mevcut değil.",
            "upgrade_to": "pro" if test_type == "ab_compare" else "business"
        }

    def check_report_access(self, user_id: int, report_type: str) -> dict:
        """Kullanıcının rapor türüne erişimi var mı?"""
        plan = self.get_user_plan(user_id)

        if not plan:
            return {
                "allowed": False,
                "message": "Aktif abonelik bulunamadı."
            }

        has_access = plan.has_feature("reports", report_type)

        if has_access:
            return {"allowed": True, "message": "Erişim var."}

        return {
            "allowed": False,
            "message": f"{report_type} raporu {plan.name} paketinde mevcut değil.",
            "upgrade_to": "pro" if report_type == "pdf" else "business"
        }

    def get_max_personas(self, user_id: int) -> int:
        """Kullanıcının tek sorguda kullanabileceği max persona sayısı"""
        plan = self.get_user_plan(user_id)
        if not plan:
            return 0
        return plan.features.get("max_personas_per_query", 50)

    def check_media_access(self, user_id: int, media_type: str) -> dict:
        """
        Kullanıcının medya türüne erişimi var mı?
        media_type: "image" veya "video"
        
        Plan features JSON'ında şu yapı beklenir:
        "media": {"image": true/false, "video": true/false}
        
        Tier erişim matrisi:
          - Starter/Basic: image=False, video=False
          - Pro/Professional: image=True, video=False
          - Business: image=True, video=True
          - Enterprise: image=True, video=True
        """
        plan = self.get_user_plan(user_id)

        if not plan:
            return {
                "allowed": False,
                "message": "Aktif abonelik bulunamadı.",
                "upgrade_to": "pro"
            }

        has_access = plan.features.get("media", {}).get(media_type, False)

        if has_access:
            return {"allowed": True, "message": "Erişim var."}

        # Yükseltme önerisi
        if media_type == "image":
            upgrade_to = "pro"
            message = f"Görsel kampanya özelliği {plan.name} paketinde mevcut değil."
        elif media_type == "video":
            upgrade_to = "business"
            message = f"Video kampanya özelliği {plan.name} paketinde mevcut değil."
        else:
            upgrade_to = "enterprise"
            message = f"{media_type} medya türü {plan.name} paketinde mevcut değil."

        return {
            "allowed": False,
            "message": message,
            "upgrade_to": upgrade_to
        }

    def _find_upgrade_plan(self, filter_name: str) -> str:
        """Filtre için gereken minimum planı bul"""
        plans = self.db.query(Plan).filter(Plan.is_active == True).order_by(Plan.price_monthly).all()
        for plan in plans:
            if plan.has_feature("filters", filter_name):
                return plan.slug
        return "enterprise"