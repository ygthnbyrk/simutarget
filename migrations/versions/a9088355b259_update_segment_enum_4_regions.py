"""update_segment_enum_4_regions

Revision ID: a9088355b259
Revises: d892920ad1e3
Create Date: 2026-03-10 22:45:00.000000

SegmentType enum güncellendi:
  ESKİ: TR, GLOBAL
  YENİ: TR, EU, USA, MENA

NOT: GLOBAL değeri kaldırılmadı (mevcut veri güvenliği için).
     Yeni kayıtlarda EU / USA / MENA kullanılacak.
"""
from typing import Sequence, Union
from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'a9088355b259'
down_revision: Union[str, Sequence[str], None] = 'd892920ad1e3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """SegmentType enum'una EU, USA, MENA değerlerini ekle."""
    op.execute("ALTER TYPE segmenttype ADD VALUE IF NOT EXISTS 'EU'")
    op.execute("ALTER TYPE segmenttype ADD VALUE IF NOT EXISTS 'USA'")
    op.execute("ALTER TYPE segmenttype ADD VALUE IF NOT EXISTS 'MENA'")

    # DecisionType enum da güncellenmiş olabilir — kontrol et
    op.execute("ALTER TYPE decisiontype ADD VALUE IF NOT EXISTS 'BUY'")
    op.execute("ALTER TYPE decisiontype ADD VALUE IF NOT EXISTS 'NO_BUY'")


def downgrade() -> None:
    """PostgreSQL enum değer silmeyi desteklemez, downgrade sadece log bırakır."""
    # PostgreSQL'de enum değeri silmek için tablo yeniden oluşturmak gerekir.
    # Bu migration geri alınamaz — gerekirse manuel müdahale gerekli.
    pass