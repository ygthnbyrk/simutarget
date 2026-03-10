"""
Agent Mining - Komut Satırı Arayüzü

Kullanım örnekleri:

  # 100 TR persona üret ve test et (DB olmadan)
  python -m src.agent_mining.cli generate --segment TR --count 100 --dry-run

  # 50K persona üret ve DB'ye kaydet
  python -m src.agent_mining.cli generate --segment TR --count 50000

  # Referans kampanyaları 500 persona üzerinde çalıştır
  python -m src.agent_mining.cli run-campaigns --persona-count 500 --segment TR

  # Maliyet tahmini (çalıştırmadan)
  python -m src.agent_mining.cli estimate --persona-count 50000 --campaign-count 10
"""

import argparse
import os
import sys

# .env dosyasını otomatik yükle
from dotenv import load_dotenv
load_dotenv()


def cmd_generate_all(args):
    """500K toplu üretim — tüm segmentler sırayla."""
    from .factory import PersonaFactory
    from .demographics import PRODUCTION_TARGETS

    print("\n🌍 500K TOPLU PERSONA ÜRETİMİ")
    print("=" * 45)
    for seg, count in PRODUCTION_TARGETS.items():
        print(f"  {seg:6} → {count:,} persona")
    print(f"  {'TOPLAM':6} → {sum(PRODUCTION_TARGETS.values()):,} persona")
    print("=" * 45)

    if args.dry_run:
        print("\n(--dry-run: sadece ilk 3 persona gösterilecek, DB'ye kaydedilmeyecek)\n")
        for seg, count in PRODUCTION_TARGETS.items():
            factory = PersonaFactory(segment=seg, seed=42)
            print(f"--- {seg} segmenti örnek ---")
            for p in factory.generate_batch(3):
                print(f"  {p.name} | {p.age}y | {p.city} | {p.income_level}")
            print()
        return

    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL tanımlı değil.")
        sys.exit(1)

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from .models import Base

    engine = create_engine(db_url)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    grand_total = 0
    import time
    start_all = time.time()

    for seg, count in PRODUCTION_TARGETS.items():
        print(f"\n▶ {seg} segmenti — {count:,} persona üretiliyor...")
        session = Session()
        factory = PersonaFactory(segment=seg)

        def progress(i, total, s=seg):
            print(f"  [{s}] {i:,}/{total:,}")

        personas = factory.generate_batch(count, progress_cb=progress)
        saved = factory.save_to_db(personas, session)
        session.close()
        grand_total += saved
        print(f"  ✅ {seg}: {saved:,} persona kaydedildi")

    elapsed = time.time() - start_all
    print(f"\n{'=' * 45}")
    print(f"  🎉 TAMAMLANDI")
    print(f"  Toplam üretilen: {grand_total:,} persona")
    print(f"  Toplam süre: {elapsed:.1f}s ({elapsed/60:.1f} dakika)")
    print(f"{'=' * 45}\n")


def cmd_generate(args):
    """Persona üretim komutu."""
    from .factory import PersonaFactory

    factory = PersonaFactory(segment=args.segment)

    print(f"\n🔧 {args.count:,} persona üretiliyor [{args.segment} segmenti]...")

    def progress(i, total):
        pct = i / total * 100
        print(f"  → {i:,}/{total:,} ({pct:.0f}%)")

    personas = factory.generate_batch(args.count, progress_cb=progress)

    print(f"\n✅ {len(personas):,} persona üretildi.")

    if args.dry_run:
        print("\n--- ÖRNEKler (ilk 5) ---")
        for p in personas[:5]:
            print(f"  {p.name} | {p.age}y | {p.city} | {p.income_level} | {p.occupation}")
            d = p.to_prompt_dict()
            print(f"  Big5: O={d['openness']} C={d['conscientiousness']} E={d['extraversion']}")
            print(f"  Değerler: {', '.join(p.values)}")
            print()
        print("(--dry-run: DB'ye kaydedilmedi)")
        return

    # DB kayıt
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL env değişkeni tanımlı değil.")
        sys.exit(1)

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from .models import Base

    engine = create_engine(db_url)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    saved = factory.save_to_db(personas, session)
    session.close()
    print(f"\n✅ {saved:,} persona veritabanına kaydedildi.")


def cmd_run_campaigns(args):
    """Referans kampanyaları çalıştırma komutu."""
    import asyncio
    from .factory import PersonaFactory
    from .runner import CampaignRunner, REFERENCE_CAMPAIGNS_SEED
    from .models import ReferenceCampaign, SegmentType, Base
    from uuid import uuid4

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY env değişkeni tanımlı değil.")
        sys.exit(1)

    # Persona üret (hızlı test için hafızada)
    print(f"\n🔧 {args.persona_count} persona üretiliyor...")
    factory = PersonaFactory(segment=args.segment)
    personas = factory.generate_batch(args.persona_count)

    # Kampanya nesneleri oluştur
    campaigns = []
    for seed in REFERENCE_CAMPAIGNS_SEED:
        target = seed.get("target_segment")
        if target and target != args.segment:
            continue
        camp = ReferenceCampaign(
            id=uuid4(),
            name=seed["name"],
            category=seed["category"],
            content=seed["content"],
            product_name=seed.get("product_name"),
            price_tl=seed.get("price_tl"),
            price_usd=seed.get("price_usd"),
        )
        campaigns.append(camp)

    print(f"📋 {len(campaigns)} kampanya bulundu.")

    # Maliyet tahmini
    est_requests = len(personas) * len(campaigns)
    est_cost = est_requests * 480 * (0.15 + 0.60 * 0.2) / 1_000_000
    print(f"💰 Tahmini maliyet: ${est_cost:.4f} ({est_requests:,} istek)")

    if not args.yes:
        confirm = input("\nDevam etmek istiyor musun? [y/N]: ")
        if confirm.lower() != "y":
            print("İptal edildi.")
            return

    # Runner
    runner = CampaignRunner(
        openai_api_key=api_key,
        model=args.model,
        max_concurrent=args.concurrency,
    )

    result = asyncio.run(runner.run_all_campaigns(campaigns, personas))
    print(f"\n🎉 Tamamlandı! {result['total_decisions']:,} karar toplandı.")


def cmd_estimate(args):
    """Maliyet tahmini komutu."""
    avg_tokens_per_request = 480
    input_price = 0.15 / 1_000_000
    output_price = 0.60 / 1_000_000
    output_ratio = 0.2  # output yaklaşık %20'si input

    total_requests = args.persona_count * args.campaign_count
    total_tokens = total_requests * avg_tokens_per_request
    input_tokens = total_tokens * (1 - output_ratio)
    output_tokens = total_tokens * output_ratio

    cost = (input_tokens * input_price) + (output_tokens * output_price)

    print(f"\n📊 MALİYET TAHMİNİ")
    print(f"  Persona sayısı:  {args.persona_count:,}")
    print(f"  Kampanya sayısı: {args.campaign_count}")
    print(f"  Toplam istek:    {total_requests:,}")
    print(f"  Toplam token:    {total_tokens:,.0f}")
    print(f"  Model:           gpt-4o-mini")
    print(f"  Tahmini maliyet: ${cost:.2f}")
    print()


def main():
    parser = argparse.ArgumentParser(description="SimuTarget Agent Mining CLI")
    subparsers = parser.add_subparsers(dest="command")

    # generate
    gen = subparsers.add_parser("generate", help="Tek segment persona üret")
    gen.add_argument("--segment", choices=["TR", "EU", "USA", "MENA"], default="TR")
    gen.add_argument("--count", type=int, default=1000)
    gen.add_argument("--dry-run", action="store_true", help="DB'ye kaydetme")

    # generate-all (500K toplu üretim)
    gen_all = subparsers.add_parser("generate-all", help="500K toplu üretim (tüm segmentler)")
    gen_all.add_argument("--dry-run", action="store_true")

    # run-campaigns
    run = subparsers.add_parser("run-campaigns", help="Referans kampanyaları çalıştır")
    run.add_argument("--segment", choices=["TR", "EU", "USA", "MENA"], default="TR")
    run.add_argument("--persona-count", type=int, default=100)
    run.add_argument("--model", default="gpt-4o-mini")
    run.add_argument("--concurrency", type=int, default=10)
    run.add_argument("--yes", "-y", action="store_true")

    # estimate
    est = subparsers.add_parser("estimate", help="Maliyet tahmini")
    est.add_argument("--persona-count", type=int, default=50000)
    est.add_argument("--campaign-count", type=int, default=10)

    args = parser.parse_args()

    if args.command == "generate":
        cmd_generate(args)
    elif args.command == "generate-all":
        cmd_generate_all(args)
    elif args.command == "run-campaigns":
        cmd_run_campaigns(args)
    elif args.command == "estimate":
        cmd_estimate(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()