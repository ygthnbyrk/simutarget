"""
Agent Mining - Campaign Runner

Referans kampanyaları persona listesine çalıştırır ve kararları toplar.

Maliyet tahmini:
  - gpt-4o-mini: input $0.15/1M token, output $0.60/1M token
  - Ortalama istek: ~400 input + ~80 output = ~480 token
  - 1000 persona × 20 kampanya = 20K istek
  - 20K × 480 token = 9.6M token total
  - Maliyet ≈ $1.44 input + $0.96 output ≈ $2.40 / 1000 persona × 20 kampanya
  - 50K persona × 20 kampanya ≈ $120 ← hedefimizle uyuşuyor
"""

import asyncio
import hashlib
import json
import time
from typing import Optional
from uuid import uuid4
from datetime import datetime

import openai

from .models import Persona, ReferenceCampaign, AgentDecision, DecisionType, CampaignStatus
from .prompts import build_prompts, parse_tr_response, parse_global_response


# ---------------------------------------------------------------------------
# REFERANS KAMPANYALAR (Hard-coded başlangıç seti)
# ---------------------------------------------------------------------------

REFERENCE_CAMPAIGNS_SEED = [
    # Teknoloji
    {
        "name": "Xiaomi Akıllı Telefon - Orta Segment",
        "category": "Teknoloji",
        "content": """Xiaomi Redmi Note 13 - 6.67" AMOLED ekran, 108MP kamera, 5000mAh batarya.
Fiyat: 12.999 TL. 12 ay taksit imkânı. Ücretsiz kargo.""",
        "product_name": "Xiaomi Redmi Note 13",
        "price_tl": 12999,
        "target_segment": "TR",
    },
    {
        "name": "iPhone 15 - Premium Segment",
        "category": "Teknoloji",
        "content": """iPhone 15 — Titanium tasarım, A16 Bionic chip, 48MP kamera sistemi.
Fiyat: 54.999 TL. Apple Trade In ile eski telefonunuzu değerlendirin.""",
        "product_name": "iPhone 15",
        "price_tl": 54999,
        "target_segment": "TR",
    },
    # Giyim
    {
        "name": "LC Waikiki Kışlık Mont",
        "category": "Tekstil/Giyim",
        "content": """LC Waikiki Su Geçirmez Mont — Şişme dolgulu, çıkarılabilir kapüşon.
Fiyat: 899 TL. Kampanya: 2 alana %20 indirim. Mağaza ve online.""",
        "product_name": "LCW Mont",
        "price_tl": 899,
        "target_segment": "TR",
    },
    # FMCG
    {
        "name": "Ülker Çikolata Aile Paketi",
        "category": "FMCG/Gıda",
        "content": """Ülker Çikolatalı Aile Paketi — 5 çeşit, 750g.
Fiyat: 189 TL. Migros'ta geçerli. Stoklar sınırlı.""",
        "product_name": "Ülker Aile Paketi",
        "price_tl": 189,
        "target_segment": "TR",
    },
    # Online Kurs
    {
        "name": "Udemy Python Kursu",
        "category": "Eğitim",
        "content": """Python ile Sıfırdan İleri Seviye — 52 saat video, sertifika.
Fiyat: 279 TL (normal 1.499 TL). 30 gün iade garantisi.""",
        "product_name": "Python Kursu",
        "price_tl": 279,
        "target_segment": "TR",
    },
    # Beyaz Eşya
    {
        "name": "Arçelik Çamaşır Makinesi",
        "category": "Beyaz Eşya",
        "content": """Arçelik 8 kg A+++ Çamaşır Makinesi — Sessize al teknolojisi, WiFi bağlantı.
Fiyat: 24.999 TL. 36 ay taksit. 10 yıl yedek parça garantisi.""",
        "product_name": "Arçelik Çamaşır Makinesi",
        "price_tl": 24999,
        "target_segment": "TR",
    },
    # Global kampanyalar
    {
        "name": "Spotify Premium Annual",
        "category": "Subscription/Entertainment",
        "content": """Spotify Premium — Ad-free music, offline downloads, high quality audio.
$9.99/month or $99.99/year (save 2 months free). Cancel anytime.""",
        "product_name": "Spotify Premium",
        "price_usd": 9.99,
        "target_segment": "GLOBAL",
    },
    {
        "name": "Amazon Echo Dot 5th Gen",
        "category": "Technology",
        "content": """Amazon Echo Dot (5th Gen) — Improved audio, built-in Eero, Alexa.
Price: $49.99. Ships free with Prime. Limited time offer.""",
        "product_name": "Echo Dot 5th Gen",
        "price_usd": 49.99,
        "target_segment": "GLOBAL",
    },
    {
        "name": "Nike Running Shoes",
        "category": "Apparel/Sports",
        "content": """Nike Air Zoom Pegasus 41 — React foam midsole, breathable upper.
Price: $130. Free shipping & 60-day returns. Available in 8 colors.""",
        "product_name": "Nike Pegasus 41",
        "price_usd": 130,
        "target_segment": "GLOBAL",
    },
    {
        "name": "HelloFresh Weekly Meal Kit",
        "category": "Food/Subscription",
        "content": """HelloFresh — Fresh ingredients, chef-designed recipes, delivered weekly.
From $8.99/serving. First box 60% off. Skip or cancel anytime.""",
        "product_name": "HelloFresh",
        "price_usd": 8.99,
        "target_segment": "GLOBAL",
    },
]


# ---------------------------------------------------------------------------
# ASYNC RUNNER
# ---------------------------------------------------------------------------

class CampaignRunner:
    """
    Referans kampanyaları persona'lara çalıştırır.
    OpenAI async API kullanır — paralel istek desteği.
    """

    def __init__(
        self,
        openai_api_key: str,
        model: str = "gpt-4o-mini",
        max_concurrent: int = 8,
        session=None,
    ):
        self.client = openai.AsyncOpenAI(api_key=openai_api_key)
        self.model = model
        self.max_concurrent = max_concurrent
        self.session = session
        self._semaphore = asyncio.Semaphore(max_concurrent)

        # İstatistikler
        self.stats = {
            "total_requests": 0,
            "successful": 0,
            "failed": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "buy_count": 0,
            "no_buy_count": 0,
        }

    async def _run_single(
        self,
        persona: Persona,
        campaign: ReferenceCampaign,
    ) -> Optional[AgentDecision]:
        """
        Tek persona × kampanya isteği gönderir.
        Hata durumunda None döner (pipeline durdurmaz).
        """
        language = "tr" if persona.segment == SegmentType.TR else "en"
        system_prompt, user_prompt = build_prompts(
            persona.to_prompt_dict(),
            campaign.content,
            language=language,
        )

        # Prompt hash (debugging için)
        prompt_hash = hashlib.sha256(system_prompt.encode()).hexdigest()[:16]

        async with self._semaphore:
            try:
                # Rate limit retry — max 5 deneme, exponential backoff
                response = None
                for attempt in range(5):
                    try:
                        response = await self.client.chat.completions.create(
                            model=self.model,
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_prompt},
                            ],
                            temperature=0.7,
                            max_tokens=150,
                            response_format={"type": "json_object"},
                        )
                        break
                    except Exception as retry_err:
                        if "rate_limit" in str(retry_err).lower() or "429" in str(retry_err):
                            wait_time = (2 ** attempt) * 0.5  # 0.5s, 1s, 2s, 4s, 8s
                            await asyncio.sleep(wait_time)
                            if attempt == 4:
                                raise
                        else:
                            raise

                raw = response.choices[0].message.content
                usage = response.usage

                # Parse
                if language == "tr":
                    parsed = parse_tr_response(raw)
                else:
                    parsed = parse_global_response(raw)

                decision_type = (
                    DecisionType.BUY if parsed["decision"] == "BUY" else DecisionType.NO_BUY
                )

                decision = AgentDecision(
                    id=uuid4(),
                    persona_id=persona.id,
                    campaign_id=campaign.id,
                    decision=decision_type,
                    confidence=min(max(parsed["confidence"], 1), 10),
                    reasoning=parsed["reasoning"][:500],  # max 500 karakter
                    system_prompt_hash=prompt_hash,
                    input_tokens=usage.prompt_tokens,
                    output_tokens=usage.completion_tokens,
                    model_used=self.model,
                )

                # İstatistik güncelle
                self.stats["successful"] += 1
                self.stats["total_input_tokens"] += usage.prompt_tokens
                self.stats["total_output_tokens"] += usage.completion_tokens
                if decision_type == DecisionType.BUY:
                    self.stats["buy_count"] += 1
                else:
                    self.stats["no_buy_count"] += 1

                return decision

            except Exception as e:
                self.stats["failed"] += 1
                print(f"  ✗ Hata [{persona.name} × {campaign.name}]: {e}")
                return None

            finally:
                self.stats["total_requests"] += 1

    async def run_campaign(
        self,
        campaign: ReferenceCampaign,
        personas: list[Persona],
        save_batch_size: int = 200,
    ) -> list[AgentDecision]:
        """
        Bir kampanyayı tüm persona'lara çalıştırır.

        Args:
            campaign: Çalıştırılacak kampanya
            personas: Persona listesi
            save_batch_size: Her kaç karardan sonra DB'ye yazılsın

        Returns:
            AgentDecision listesi
        """
        print(f"\n▶ Kampanya: '{campaign.name}'")
        print(f"  {len(personas)} persona × 1 kampanya = {len(personas)} istek")

        campaign.status = CampaignStatus.RUNNING
        if self.session:
            self.session.commit()

        tasks = [self._run_single(persona, campaign) for persona in personas]
        decisions = []
        start = time.time()

        # asyncio.gather ile paralel çalıştır
        results = await asyncio.gather(*tasks)

        for decision in results:
            if decision:
                decisions.append(decision)

        # DB kayıt
        if self.session and decisions:
            for i in range(0, len(decisions), save_batch_size):
                batch = decisions[i:i + save_batch_size]
                self.session.bulk_save_objects(batch)
                self.session.commit()

        # Kampanya istatistiklerini güncelle
        campaign.total_personas_run = len(decisions)
        campaign.buy_count = sum(1 for d in decisions if d.decision == DecisionType.BUY)
        campaign.no_buy_count = campaign.total_personas_run - campaign.buy_count
        campaign.status = CampaignStatus.COMPLETED
        campaign.completed_at = datetime.utcnow()

        if self.session:
            self.session.commit()

        elapsed = time.time() - start
        buy_rate = campaign.buy_rate
        print(f"  ✓ Tamamlandı — {len(decisions)} karar | Satın alma oranı: %{buy_rate*100:.1f} | {elapsed:.1f}s")

        return decisions

    async def run_all_campaigns(
        self,
        campaigns: list[ReferenceCampaign],
        personas: list[Persona],
    ) -> dict:
        """
        Tüm kampanyaları persona listesine sırayla çalıştırır.

        Returns:
            Özet istatistik dict
        """
        all_decisions = []
        for campaign in campaigns:
            decisions = await self.run_campaign(campaign, personas)
            all_decisions.extend(decisions)

        total_cost_usd = self._estimate_cost()
        print(f"\n{'='*50}")
        print(f"  ÖZET")
        print(f"  Toplam istek: {self.stats['total_requests']}")
        print(f"  Başarılı: {self.stats['successful']}")
        print(f"  Başarısız: {self.stats['failed']}")
        print(f"  Toplam token: {self.stats['total_input_tokens'] + self.stats['total_output_tokens']:,}")
        print(f"  Tahmini maliyet: ${total_cost_usd:.4f}")
        print(f"{'='*50}\n")

        return {
            "stats": self.stats,
            "estimated_cost_usd": total_cost_usd,
            "total_decisions": len(all_decisions),
        }

    def _estimate_cost(self) -> float:
        """gpt-4o-mini fiyatlandırmasına göre maliyet tahmini."""
        input_cost = self.stats["total_input_tokens"] * 0.15 / 1_000_000
        output_cost = self.stats["total_output_tokens"] * 0.60 / 1_000_000
        return input_cost + output_cost


# ---------------------------------------------------------------------------
# SYNC WRAPPER (CLI / test için)
# ---------------------------------------------------------------------------

def run_campaign_sync(
    campaign: ReferenceCampaign,
    personas: list[Persona],
    api_key: str,
    model: str = "gpt-4o-mini",
    max_concurrent: int = 8,
    session=None,
) -> list[AgentDecision]:
    """asyncio event loop olmayan ortamlar için sync wrapper."""
    runner = CampaignRunner(api_key, model, max_concurrent, session)
    return asyncio.run(runner.run_campaign(campaign, personas))


# Import guard
from .models import SegmentType  # noqa — döngüsel import önlemi
