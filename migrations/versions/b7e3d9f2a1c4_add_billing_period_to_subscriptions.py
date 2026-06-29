"""add billing_period to subscriptions (oturum #8.4)

Yıllık plan desteği için her aboneliğin aylık mı yıllık mı olduğunu işaretler.
Üç yerde kullanılır:
  - MRR normalizasyonu (yearly → price_yearly / 12)
  - Renewal dönem uzunluğu (yearly → +365 gün, monthly → +30 gün)
  - Kredi miktarı (yearly → credits_monthly * 12 peşin, Option A)

Mevcut tüm abonelikler aylıktı → server_default='monthly' ile doğru doldurulur.

Revision ID: b7e3d9f2a1c4
Revises: c2d8f1a9e4b7
Create Date: 2026-06-29
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b7e3d9f2a1c4"
down_revision = "c2d8f1a9e4b7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "subscriptions",
        sa.Column(
            "billing_period",
            sa.String(length=20),
            nullable=False,
            server_default="monthly",
        ),
    )


def downgrade() -> None:
    op.drop_column("subscriptions", "billing_period")
