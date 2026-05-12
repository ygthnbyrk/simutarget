"""add_google_oauth_fields

Revision ID: a8b3c5d2e7f1
Revises: d892920ad1e3
Create Date: 2026-05-12 14:50:00.000000

Google OAuth desteği için users tablosuna 2 yeni kolon ekler:
- google_id: Google'dan gelen unique kullanıcı ID (varchar, unique, nullable)
- auth_provider: "email" veya "google" (default "email")

Ayrıca password_hash'i NULLABLE yapar — Google ile kayıt olan kullanıcıların
şifresi olmayacak.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a8b3c5d2e7f1'
down_revision: Union[str, Sequence[str], None] = 'd892920ad1e3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. google_id kolonu (nullable, unique)
    op.add_column(
        'users',
        sa.Column('google_id', sa.String(length=100), nullable=True)
    )
    op.create_index(
        op.f('ix_users_google_id'),
        'users',
        ['google_id'],
        unique=True,
    )

    # 2. auth_provider kolonu (default "email")
    op.add_column(
        'users',
        sa.Column(
            'auth_provider',
            sa.String(length=20),
            nullable=False,
            server_default='email',
        )
    )

    # 3. password_hash NULLABLE yap — Google ile kayıt olanlar için şifre yok
    op.alter_column(
        'users',
        'password_hash',
        existing_type=sa.String(length=255),
        nullable=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    # 1. password_hash tekrar NOT NULL
    # NOT: Bu downgrade Google ile kayıt olmuş user'larda fail edebilir
    # (password_hash NULL kalanlar varsa). Production'da downgrade nadiren çalıştırılır,
    # gerekirse önce manuel temizlik gerekir.
    op.alter_column(
        'users',
        'password_hash',
        existing_type=sa.String(length=255),
        nullable=False,
    )

    # 2. auth_provider kolonunu sil
    op.drop_column('users', 'auth_provider')

    # 3. google_id index ve kolonunu sil
    op.drop_index(op.f('ix_users_google_id'), table_name='users')
    op.drop_column('users', 'google_id')
