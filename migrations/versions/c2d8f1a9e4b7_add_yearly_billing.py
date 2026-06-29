"""add yearly billing to plans (oturum #8.4)

- plans tablosuna price_yearly + lemonsqueezy_yearly_variant_id kolonları eklenir.
- Aylık variant ID'leri düzeltilir: LS'te variant'lar yeniden oluşturulduğu için
  DB'deki eski aylık ID'ler (1700900/1700899/1700897) artık yanlış/ölü.
    starter:  1700900 (LS'te yok)        -> 1850202
    pro:      1700899 (artık yıllık oldu) -> 1850206
    business: 1700897 (artık yıllık oldu) -> 1850210
- Yıllık değerler doldurulur (price_yearly dolar cinsinden, model Numeric(10,2)):
    starter:  499.90  / variant 1850168
    pro:      1499.90 / variant 1700899
    business: 3999.90 / variant 1700897

Disposable (id=5) ve Enterprise (id=9) bu migration'da DEĞİŞTİRİLMEZ.

Revision ID: c2d8f1a9e4b7
Revises: e3f7a2c9b1d4
Create Date: 2026-06-29
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "c2d8f1a9e4b7"
down_revision = "e3f7a2c9b1d4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1) Yeni kolonlar (nullable — mevcut satırları bozmaz)
    op.add_column(
        "plans",
        sa.Column("price_yearly", sa.Numeric(10, 2), nullable=True),
    )
    op.add_column(
        "plans",
        sa.Column("lemonsqueezy_yearly_variant_id", sa.String(length=100), nullable=True),
    )
    op.create_index(
        "ix_plans_lemonsqueezy_yearly_variant_id",
        "plans",
        ["lemonsqueezy_yearly_variant_id"],
        unique=True,
    )

    # 2) Veri düzeltme + doldurma (her plan tek UPDATE'te — atomik, unique çakışması yok)
    op.execute(
        """
        UPDATE plans
           SET lemonsqueezy_variant_id = '1850202',
               price_yearly = 499.90,
               lemonsqueezy_yearly_variant_id = '1850168'
         WHERE slug = 'starter';
        """
    )
    op.execute(
        """
        UPDATE plans
           SET lemonsqueezy_variant_id = '1850206',
               price_yearly = 1499.90,
               lemonsqueezy_yearly_variant_id = '1700899'
         WHERE slug = 'pro';
        """
    )
    op.execute(
        """
        UPDATE plans
           SET lemonsqueezy_variant_id = '1850210',
               price_yearly = 3999.90,
               lemonsqueezy_yearly_variant_id = '1700897'
         WHERE slug = 'business';
        """
    )


def downgrade() -> None:
    # Veriyi eski haline döndür (aylık ID'ler eski/ölü değerlere geri yazılır)
    op.execute(
        """
        UPDATE plans
           SET lemonsqueezy_variant_id = '1700900',
               price_yearly = NULL,
               lemonsqueezy_yearly_variant_id = NULL
         WHERE slug = 'starter';
        """
    )
    op.execute(
        """
        UPDATE plans
           SET lemonsqueezy_variant_id = '1700899',
               price_yearly = NULL,
               lemonsqueezy_yearly_variant_id = NULL
         WHERE slug = 'pro';
        """
    )
    op.execute(
        """
        UPDATE plans
           SET lemonsqueezy_variant_id = '1700897',
               price_yearly = NULL,
               lemonsqueezy_yearly_variant_id = NULL
         WHERE slug = 'business';
        """
    )

    # Kolonları kaldır
    op.drop_index("ix_plans_lemonsqueezy_yearly_variant_id", table_name="plans")
    op.drop_column("plans", "lemonsqueezy_yearly_variant_id")
    op.drop_column("plans", "price_yearly")
