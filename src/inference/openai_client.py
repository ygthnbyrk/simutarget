"""OpenAI API client for persona-based campaign evaluation."""

import os
import json
import asyncio
from typing import Optional, List
from dataclasses import dataclass
from openai import OpenAI, AsyncOpenAI

from ..personas.models import Persona, PersonaDecision, ComparisonResult
from .prompts import (
    build_persona_system_prompt,
    build_campaign_evaluation_prompt,
    build_campaign_evaluation_prompt_with_image,
    build_comparison_prompt_with_image,
    build_quick_evaluation_prompt,
    build_comparison_prompt,
    build_openai_messages_with_image,
    parse_decision_response,
)


@dataclass
class EvaluationResult:
    """Tek bir değerlendirme sonucu."""
    persona: Persona
    decision: Optional[PersonaDecision]
    raw_response: str
    success: bool
    error: Optional[str] = None


@dataclass
class CampaignTestResult:
    """Kampanya test sonuçları özeti."""
    campaign_id: str
    campaign_content: str
    total_personas: int
    successful_evaluations: int
    failed_evaluations: int
    yes_count: int
    no_count: int
    conversion_rate: float
    avg_confidence: float
    results: List[EvaluationResult]
    
    def summary(self) -> dict:
        """Özet istatistikler."""
        return {
            "campaign_id": self.campaign_id,
            "total": self.total_personas,
            "success_rate": f"{(self.successful_evaluations / self.total_personas) * 100:.1f}%",
            "conversion_rate": f"{self.conversion_rate:.1f}%",
            "yes_votes": self.yes_count,
            "no_votes": self.no_count,
            "avg_confidence": f"{self.avg_confidence:.1f}/10",
        }


class SimuTargetLLM:
    """
    SimuTarget LLM Client.
    Personaları kullanarak kampanya değerlendirmesi yapar.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: int = 500,
    ):
        """
        Args:
            api_key: OpenAI API anahtarı (veya OPENAI_API_KEY env var)
            model: Kullanılacak model (gpt-4o-mini önerilen)
            temperature: Yaratıcılık seviyesi (0.0-1.0)
            max_tokens: Maksimum yanıt uzunluğu
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key gerekli! OPENAI_API_KEY env var veya api_key parametresi kullanın.")
        
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Sync ve async clientlar
        self.client = OpenAI(api_key=self.api_key)
        self.async_client = AsyncOpenAI(api_key=self.api_key)
    
    def evaluate_campaign(
        self,
        persona: Persona,
        campaign_content: str,
        campaign_id: str = "test_campaign",
        verbose: bool = False,
        lang: str = "tr",
        image_base64: str = None,
    ) -> EvaluationResult:
        """
        Tek bir persona ile kampanya değerlendirmesi yapar.
        Görsel varsa GPT-4o vision ile multimodal değerlendirme yapar.
        
        Args:
            persona: Değerlendirme yapacak persona
            campaign_content: Kampanya içeriği (metin, reklam metni vb.)
            campaign_id: Kampanya tanımlayıcısı
            verbose: Detaylı çıktı
            lang: Dil (en, tr)
            image_base64: Base64 encoded görsel (opsiyonel)
        
        Returns:
            EvaluationResult objesi
        """
        try:
            # Promptları oluştur
            system_prompt = build_persona_system_prompt(persona, lang=lang)
            
            if image_base64:
                # Görsel var — multimodal prompt + vision model
                user_prompt = build_campaign_evaluation_prompt_with_image(
                    campaign_content, lang=lang
                )
                messages = build_openai_messages_with_image(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    image_base64=image_base64,
                )
                # Vision için gpt-4o kullan (gpt-4o-mini de vision destekliyor)
                model = self.model if "gpt-4o" in self.model else "gpt-4o-mini"
            else:
                # Sadece metin — standart prompt
                user_prompt = build_campaign_evaluation_prompt(campaign_content, lang=lang)
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
                model = self.model
            
            if verbose:
                print(f"\n🎭 Persona: {persona.name} ({persona.age}, {persona.occupation})")
                print(f"📍 Lokasyon: {persona.city}, {persona.country}")
                if image_base64:
                    print(f"🖼️  Görsel kampanya (vision mode)")
                if persona.primary_anxiety:
                    print(f"😰 Endişe: {persona.primary_anxiety.name}")
            
            # API çağrısı
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            
            raw_response = response.choices[0].message.content
            
            # Yanıtı parse et
            decision = parse_decision_response(persona, campaign_id, raw_response)
            
            if verbose and decision:
                emoji = "✅" if decision.decision else "❌"
                print(f"{emoji} Karar: {'EVET' if decision.decision else 'HAYIR'} (Güven: {decision.confidence}/10)")
                print(f"💬 Gerekçe: {decision.reasoning}")
                if decision.anxiety_impact:
                    print(f"😰 Endişe etkisi: {decision.anxiety_impact}")
            
            return EvaluationResult(
                persona=persona,
                decision=decision,
                raw_response=raw_response,
                success=decision is not None,
            )
            
        except Exception as e:
            if verbose:
                print(f"❌ Hata: {e}")
            return EvaluationResult(
                persona=persona,
                decision=None,
                raw_response="",
                success=False,
                error=str(e),
            )
    
    async def evaluate_campaign_async(
        self,
        persona: Persona,
        campaign_content: str,
        campaign_id: str = "test_campaign",
        lang: str = "tr",
        image_base64: str = None,
    ) -> EvaluationResult:
        """
        Asenkron kampanya değerlendirmesi.
        Batch işlemler için kullanılır.
        """
        try:
            system_prompt = build_persona_system_prompt(persona, lang=lang)
            
            if image_base64:
                user_prompt = build_campaign_evaluation_prompt_with_image(
                    campaign_content, lang=lang
                )
                messages = build_openai_messages_with_image(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    image_base64=image_base64,
                )
                model = self.model if "gpt-4o" in self.model else "gpt-4o-mini"
            else:
                user_prompt = build_campaign_evaluation_prompt(campaign_content, lang=lang)
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
                model = self.model
            
            response = await self.async_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            
            raw_response = response.choices[0].message.content
            decision = parse_decision_response(persona, campaign_id, raw_response)
            
            return EvaluationResult(
                persona=persona,
                decision=decision,
                raw_response=raw_response,
                success=decision is not None,
            )
            
        except Exception as e:
            return EvaluationResult(
                persona=persona,
                decision=None,
                raw_response="",
                success=False,
                error=str(e),
            )
    
    def test_campaign(
        self,
        personas: List[Persona],
        campaign_content: str,
        campaign_id: str = "test_campaign",
        verbose: bool = True,
        lang: str = "tr",
        image_base64: str = None,
    ) -> CampaignTestResult:
        """
        Birden fazla persona ile kampanya testi yapar (senkron).
        
        Args:
            personas: Test edilecek persona listesi
            campaign_content: Kampanya içeriği
            campaign_id: Kampanya ID
            verbose: İlerleme göster
            lang: Dil
            image_base64: Base64 encoded görsel (opsiyonel)
        
        Returns:
            CampaignTestResult objesi
        """
        results = []
        yes_count = 0
        no_count = 0
        total_confidence = 0
        successful = 0
        
        if verbose:
            print(f"\n{'='*60}")
            print(f"🎯 KAMPANYA TESTİ BAŞLIYOR")
            if image_base64:
                print(f"🖼️  Görsel kampanya modu aktif")
            print(f"{'='*60}")
            print(f"📢 Kampanya: {campaign_content[:100]}...")
            print(f"👥 Persona sayısı: {len(personas)}")
            print(f"{'='*60}\n")
        
        for i, persona in enumerate(personas):
            if verbose:
                print(f"\n[{i+1}/{len(personas)}] Değerlendiriliyor...")
            
            result = self.evaluate_campaign(
                persona=persona,
                campaign_content=campaign_content,
                campaign_id=campaign_id,
                verbose=verbose,
                lang=lang,
                image_base64=image_base64,
            )
            results.append(result)
            
            if result.success and result.decision:
                successful += 1
                total_confidence += result.decision.confidence
                if result.decision.decision:
                    yes_count += 1
                else:
                    no_count += 1
        
        conversion_rate = (yes_count / successful * 100) if successful > 0 else 0
        avg_confidence = (total_confidence / successful) if successful > 0 else 0
        
        test_result = CampaignTestResult(
            campaign_id=campaign_id,
            campaign_content=campaign_content,
            total_personas=len(personas),
            successful_evaluations=successful,
            failed_evaluations=len(personas) - successful,
            yes_count=yes_count,
            no_count=no_count,
            conversion_rate=conversion_rate,
            avg_confidence=avg_confidence,
            results=results,
        )
        
        if verbose:
            print(f"\n{'='*60}")
            print(f"📊 TEST SONUÇLARI")
            print(f"{'='*60}")
            summary = test_result.summary()
            for key, value in summary.items():
                print(f"  {key}: {value}")
            print(f"{'='*60}\n")
        
        return test_result
    
    async def test_campaign_async(
        self,
        personas: List[Persona],
        campaign_content: str,
        campaign_id: str = "test_campaign",
        max_concurrent: int = 10,
        verbose: bool = True,
        lang: str = "tr",
        image_base64: str = None,
    ) -> CampaignTestResult:
        """
        Asenkron kampanya testi - paralel işlem.
        Büyük persona setleri için önerilir.
        
        Args:
            personas: Test edilecek persona listesi
            campaign_content: Kampanya içeriği
            campaign_id: Kampanya ID
            max_concurrent: Maksimum paralel istek sayısı
            verbose: İlerleme göster
            lang: Dil
            image_base64: Base64 encoded görsel (opsiyonel)
        """
        if verbose:
            print(f"\n🚀 Asenkron test başlıyor ({len(personas)} persona, max {max_concurrent} paralel)")
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def limited_evaluate(persona: Persona) -> EvaluationResult:
            async with semaphore:
                return await self.evaluate_campaign_async(
                    persona=persona,
                    campaign_content=campaign_content,
                    campaign_id=campaign_id,
                    lang=lang,
                    image_base64=image_base64,
                )
        
        # Tüm işlemleri paralel başlat
        tasks = [limited_evaluate(p) for p in personas]
        results = await asyncio.gather(*tasks)
        
        # Sonuçları hesapla
        yes_count = sum(1 for r in results if r.success and r.decision and r.decision.decision)
        no_count = sum(1 for r in results if r.success and r.decision and not r.decision.decision)
        successful = sum(1 for r in results if r.success)
        total_confidence = sum(r.decision.confidence for r in results if r.success and r.decision)
        
        conversion_rate = (yes_count / successful * 100) if successful > 0 else 0
        avg_confidence = (total_confidence / successful) if successful > 0 else 0
        
        test_result = CampaignTestResult(
            campaign_id=campaign_id,
            campaign_content=campaign_content,
            total_personas=len(personas),
            successful_evaluations=successful,
            failed_evaluations=len(personas) - successful,
            yes_count=yes_count,
            no_count=no_count,
            conversion_rate=conversion_rate,
            avg_confidence=avg_confidence,
            results=list(results),
        )
        
        if verbose:
            print(f"\n✅ Test tamamlandı!")
            summary = test_result.summary()
            for key, value in summary.items():
                print(f"  {key}: {value}")
        
        return test_result
    
    def compare_campaigns(
        self,
        persona: Persona,
        campaign_a: str,
        campaign_b: str,
        verbose: bool = False,
        lang: str = "tr",
        image_a_base64: str = None,
        image_b_base64: str = None,
    ) -> ComparisonResult:
        """
        İki kampanya/seçeneği karşılaştırır (A/B test).
        Görsel destekli — bir veya iki seçenek görsel içerebilir.
        """
        from datetime import datetime
        
        try:
            system_prompt = build_persona_system_prompt(persona, lang=lang)
            
            has_any_image = image_a_base64 or image_b_base64
            
            if has_any_image:
                # Multimodal karşılaştırma
                user_prompt = build_comparison_prompt_with_image(
                    campaign_a, campaign_b,
                    has_image_a=bool(image_a_base64),
                    has_image_b=bool(image_b_base64),
                    persona=persona,
                    lang=lang,
                )
                
                # Görselleri topla
                images = []
                if image_a_base64:
                    images.append({"base64": image_a_base64})
                if image_b_base64:
                    images.append({"base64": image_b_base64})
                
                messages = build_openai_messages_with_image(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    image_base64=images[0]["base64"] if len(images) == 1 else None,
                    additional_images=images if len(images) > 1 else None,
                )
                model = self.model if "gpt-4o" in self.model else "gpt-4o-mini"
            else:
                user_prompt = build_comparison_prompt(campaign_a, campaign_b, persona, lang=lang)
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
                model = self.model
            
            if verbose:
                print(f"\n🎭 {persona.name} ({persona.age}, {persona.occupation})")
                if has_any_image:
                    print(f"🖼️  Görsel A/B karşılaştırma")
                if persona.political_view:
                    print(f"🗳️  Siyasi görüş: {persona.political_view}")
            
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            
            raw_response = response.choices[0].message.content
            
            # JSON parse
            import re
            json_match = re.search(r'\{[^{}]*\}', raw_response, re.DOTALL)
            
            if json_match:
                data = json.loads(json_match.group())
                
                choice = data.get("tercih", "HİÇBİRİ").upper()
                if choice not in ["A", "B", "HİÇBİRİ", "NONE"]:
                    choice = "HİÇBİRİ"
                if choice == "NONE":
                    choice = "HİÇBİRİ"
                
                confidence = int(data.get("guven", 5))
                confidence = max(1, min(10, confidence))
                
                a_score = int(data.get("a_puani", 5))
                b_score = int(data.get("b_puani", 5))
                
                result = ComparisonResult(
                    persona_id=persona.id,
                    persona_name=persona.name,
                    persona_political_view=persona.political_view,
                    persona_age=persona.age,
                    persona_gender=persona.gender,
                    persona_occupation=persona.occupation,
                    choice=choice,
                    confidence=confidence,
                    reasoning=json.dumps({"tr": data.get("gerekce_tr", data.get("gerekce", "Belirtilmemiş")), "en": data.get("gerekce_en", data.get("gerekce", "Not specified"))}, ensure_ascii=False),
                    option_scores={"A": a_score, "B": b_score},
                    influencing_factors=data.get("etkileyen_faktorler", []),
                    political_influence=data.get("siyasi_etki"),
                    timestamp=datetime.now().isoformat()
                )
                
                if verbose:
                    emoji = "🔵" if choice == "A" else "🔴" if choice == "B" else "⚪"
                    print(f"{emoji} Tercih: {choice} (Güven: {confidence}/10)")
                    print(f"💬 {result.reasoning[:100]}...")
                
                return result
            
            # Parse başarısız
            return ComparisonResult(
                persona_id=persona.id,
                persona_name=persona.name,
                persona_political_view=persona.political_view,
                persona_age=persona.age,
                persona_gender=persona.gender,
                persona_occupation=persona.occupation,
                choice="HİÇBİRİ",
                confidence=1,
                reasoning="Parse hatası",
                option_scores={"A": 0, "B": 0},
                influencing_factors=[],
                political_influence=None,
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            from datetime import datetime
            if verbose:
                print(f"❌ Hata: {e}")
            return ComparisonResult(
                persona_id=persona.id,
                persona_name=persona.name,
                persona_political_view=persona.political_view,
                persona_age=persona.age,
                persona_gender=persona.gender,
                persona_occupation=persona.occupation,
                choice="HİÇBİRİ",
                confidence=1,
                reasoning=f"Hata: {str(e)}",
                option_scores={"A": 0, "B": 0},
                influencing_factors=[],
                political_influence=None,
                timestamp=datetime.now().isoformat()
            )

    def multi_compare_campaigns(
        self,
        persona: Persona,
        campaigns: dict[str, str],
        verbose: bool = False,
        lang: str = "tr",
    ) -> ComparisonResult:
        """
        3+ kampanya/secenegi karsilastirir (A/B/C veya A/B/C/D test).
        """
        from datetime import datetime
        from .prompts import build_multi_comparison_prompt
        
        try:
            system_prompt = build_persona_system_prompt(persona, lang=lang)
            user_prompt = build_multi_comparison_prompt(campaigns, persona, lang=lang)
            
            if verbose:
                print(f"\n🎭 {persona.name} ({persona.age}, {persona.occupation})")
                if persona.political_view:
                    print(f"🗳️  Siyasi gorus: {persona.political_view}")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            
            raw_response = response.choices[0].message.content
            
            # JSON parse
            import re
            json_match = re.search(r'\{[^{}]*\}', raw_response, re.DOTALL)
            
            if json_match:
                data = json.loads(json_match.group())
                
                valid_choices = list(campaigns.keys()) + ["HICBIRI", "NONE"]
                choice = data.get("tercih", "HICBIRI").upper()
                if choice not in valid_choices:
                    choice = "HICBIRI"
                if choice == "NONE":
                    choice = "HICBIRI"
                
                confidence = int(data.get("guven", 5))
                confidence = max(1, min(10, confidence))
                
                # Tum seceneklerin puanlarini al
                option_scores = {}
                for label in campaigns.keys():
                    score_key = f"{label.lower()}_puani"
                    option_scores[label] = int(data.get(score_key, 5))
                
                result = ComparisonResult(
                    persona_id=persona.id,
                    persona_name=persona.name,
                    persona_political_view=persona.political_view,
                    persona_age=persona.age,
                    persona_gender=persona.gender.value if hasattr(persona.gender, 'value') else str(persona.gender),
                    persona_occupation=persona.occupation,
                    choice=choice,
                    confidence=confidence,
                    reasoning=json.dumps({"tr": data.get("gerekce_tr", data.get("gerekce", "Belirtilmemis")), "en": data.get("gerekce_en", data.get("gerekce", "Not specified"))}, ensure_ascii=False),
                    option_scores=option_scores,
                    influencing_factors=data.get("etkileyen_faktorler", []),
                    political_influence=data.get("siyasi_etki"),
                    timestamp=datetime.now().isoformat()
                )
                
                if verbose:
                    emojis = {"A": "🔵", "B": "🔴", "C": "🟢", "D": "🟡"}
                    emoji = emojis.get(choice, "⚪")
                    print(f"{emoji} Tercih: {choice} (Guven: {confidence}/10)")
                    print(f"💬 {result.reasoning[:100]}...")
                
                return result
            
            # Parse basarisiz
            return ComparisonResult(
                persona_id=persona.id,
                persona_name=persona.name,
                persona_political_view=persona.political_view,
                persona_age=persona.age,
                persona_gender=persona.gender.value if hasattr(persona.gender, 'value') else str(persona.gender),
                persona_occupation=persona.occupation,
                choice="HICBIRI",
                confidence=1,
                reasoning="Parse hatasi",
                option_scores={label: 0 for label in campaigns.keys()},
                influencing_factors=[],
                political_influence=None,
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            from datetime import datetime
            if verbose:
                print(f"❌ Hata: {e}")
            return ComparisonResult(
                persona_id=persona.id,
                persona_name=persona.name,
                persona_political_view=persona.political_view,
                persona_age=persona.age,
                persona_gender=persona.gender.value if hasattr(persona.gender, 'value') else str(persona.gender),
                persona_occupation=persona.occupation,
                choice="HICBIRI",
                confidence=1,
                reasoning=f"Hata: {str(e)}",
                option_scores={label: 0 for label in campaigns.keys()},
                influencing_factors=[],
                political_influence=None,
                timestamp=datetime.now().isoformat()
            )

    async def compare_campaigns_async(
        self,
        persona: Persona,
        campaign_a: str,
        campaign_b: str,
        lang: str = "tr",
        image_a_base64: str = None,
        image_b_base64: str = None,
    ) -> ComparisonResult:
        """Asenkron A/B karşılaştırma — paralel batch için."""
        from datetime import datetime
        
        try:
            system_prompt = build_persona_system_prompt(persona, lang=lang)
            has_any_image = image_a_base64 or image_b_base64
            
            if has_any_image:
                user_prompt = build_comparison_prompt_with_image(
                    campaign_a, campaign_b,
                    has_image_a=bool(image_a_base64),
                    has_image_b=bool(image_b_base64),
                    persona=persona, lang=lang,
                )
                images = []
                if image_a_base64:
                    images.append({"base64": image_a_base64})
                if image_b_base64:
                    images.append({"base64": image_b_base64})
                messages = build_openai_messages_with_image(
                    system_prompt=system_prompt, user_prompt=user_prompt,
                    image_base64=images[0]["base64"] if len(images) == 1 else None,
                    additional_images=images if len(images) > 1 else None,
                )
                model = self.model if "gpt-4o" in self.model else "gpt-4o-mini"
            else:
                user_prompt = build_comparison_prompt(campaign_a, campaign_b, persona, lang=lang)
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
                model = self.model
            
            response = await self.async_client.chat.completions.create(
                model=model, messages=messages,
                temperature=self.temperature, max_tokens=self.max_tokens,
            )
            
            raw_response = response.choices[0].message.content
            
            import re
            json_match = re.search(r'\{[^{}]*\}', raw_response, re.DOTALL)
            
            if json_match:
                data = json.loads(json_match.group())
                choice = data.get("tercih", "HİÇBİRİ").upper()
                if choice not in ["A", "B", "HİÇBİRİ", "NONE"]:
                    choice = "HİÇBİRİ"
                if choice == "NONE":
                    choice = "HİÇBİRİ"
                confidence = max(1, min(10, int(data.get("guven", 5))))
                a_score = int(data.get("a_puani", 5))
                b_score = int(data.get("b_puani", 5))
                
                return ComparisonResult(
                    persona_id=persona.id, persona_name=persona.name,
                    persona_political_view=persona.political_view,
                    persona_age=persona.age, persona_gender=persona.gender,
                    persona_occupation=persona.occupation,
                    choice=choice, confidence=confidence,
                    reasoning=json.dumps({"tr": data.get("gerekce_tr", data.get("gerekce", "Belirtilmemiş")), "en": data.get("gerekce_en", data.get("gerekce", "Not specified"))}, ensure_ascii=False),
                    option_scores={"A": a_score, "B": b_score},
                    influencing_factors=data.get("etkileyen_faktorler", []),
                    political_influence=data.get("siyasi_etki"),
                    timestamp=datetime.now().isoformat()
                )
            
            return ComparisonResult(
                persona_id=persona.id, persona_name=persona.name,
                persona_political_view=persona.political_view,
                persona_age=persona.age, persona_gender=persona.gender,
                persona_occupation=persona.occupation,
                choice="HİÇBİRİ", confidence=1, reasoning="Parse hatası",
                option_scores={"A": 0, "B": 0}, influencing_factors=[],
                political_influence=None, timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            from datetime import datetime
            return ComparisonResult(
                persona_id=persona.id, persona_name=persona.name,
                persona_political_view=persona.political_view,
                persona_age=persona.age, persona_gender=persona.gender,
                persona_occupation=persona.occupation,
                choice="HİÇBİRİ", confidence=1, reasoning=f"Hata: {str(e)}",
                option_scores={"A": 0, "B": 0}, influencing_factors=[],
                political_influence=None, timestamp=datetime.now().isoformat()
            )

    async def multi_compare_campaigns_async(
        self,
        persona: Persona,
        campaigns: dict[str, str],
        lang: str = "tr",
    ) -> ComparisonResult:
        """Asenkron multi karşılaştırma — paralel batch için."""
        from datetime import datetime
        from .prompts import build_multi_comparison_prompt
        
        try:
            system_prompt = build_persona_system_prompt(persona, lang=lang)
            user_prompt = build_multi_comparison_prompt(campaigns, persona, lang=lang)
            
            response = await self.async_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature, max_tokens=self.max_tokens,
            )
            
            raw_response = response.choices[0].message.content
            
            import re
            json_match = re.search(r'\{[^{}]*\}', raw_response, re.DOTALL)
            
            if json_match:
                data = json.loads(json_match.group())
                valid_choices = list(campaigns.keys()) + ["HICBIRI", "NONE"]
                choice = data.get("tercih", "HICBIRI").upper()
                if choice not in valid_choices:
                    choice = "HICBIRI"
                if choice == "NONE":
                    choice = "HICBIRI"
                confidence = max(1, min(10, int(data.get("guven", 5))))
                option_scores = {}
                for label in campaigns.keys():
                    option_scores[label] = int(data.get(f"{label.lower()}_puani", 5))
                
                return ComparisonResult(
                    persona_id=persona.id, persona_name=persona.name,
                    persona_political_view=persona.political_view,
                    persona_age=persona.age,
                    persona_gender=persona.gender.value if hasattr(persona.gender, 'value') else str(persona.gender),
                    persona_occupation=persona.occupation,
                    choice=choice, confidence=confidence,
                    reasoning=json.dumps({"tr": data.get("gerekce_tr", data.get("gerekce", "Belirtilmemis")), "en": data.get("gerekce_en", data.get("gerekce", "Not specified"))}, ensure_ascii=False),
                    option_scores=option_scores,
                    influencing_factors=data.get("etkileyen_faktorler", []),
                    political_influence=data.get("siyasi_etki"),
                    timestamp=datetime.now().isoformat()
                )
            
            return ComparisonResult(
                persona_id=persona.id, persona_name=persona.name,
                persona_political_view=persona.political_view,
                persona_age=persona.age,
                persona_gender=persona.gender.value if hasattr(persona.gender, 'value') else str(persona.gender),
                persona_occupation=persona.occupation,
                choice="HICBIRI", confidence=1, reasoning="Parse hatasi",
                option_scores={label: 0 for label in campaigns.keys()},
                influencing_factors=[], political_influence=None,
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            from datetime import datetime
            return ComparisonResult(
                persona_id=persona.id, persona_name=persona.name,
                persona_political_view=persona.political_view,
                persona_age=persona.age,
                persona_gender=persona.gender.value if hasattr(persona.gender, 'value') else str(persona.gender),
                persona_occupation=persona.occupation,
                choice="HICBIRI", confidence=1, reasoning=f"Hata: {str(e)}",
                option_scores={label: 0 for label in campaigns.keys()},
                influencing_factors=[], political_influence=None,
                timestamp=datetime.now().isoformat()
            )


def run_async_test(
    llm: SimuTargetLLM,
    personas: List[Persona],
    campaign_content: str,
    campaign_id: str = "test_campaign",
    max_concurrent: int = 5,
) -> CampaignTestResult:
    """
    Asenkron testi senkron ortamda çalıştırmak için helper.
    """
    return asyncio.run(
        llm.test_campaign_async(
            personas=personas,
            campaign_content=campaign_content,
            campaign_id=campaign_id,
            max_concurrent=max_concurrent,
        )
    )