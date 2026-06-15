"""add password_reset_tokens table

Revision ID: e3f7a2c9b1d4
Revises: a8b3c5d2e7f1
Create Date: 2026-06-15

Oturum #8.3 — Forgot Password implementasyonu.
Şifre sıfırlama token'larını saklar. Ham token kullanıcıya email ile gider,
DB'ye yalnızca SHA256 hash yazılır (DB sızsa bile token kullanılamaz).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e3f7a2c9b1d4'
down_revision: Union[str, Sequence[str], None] = 'a8b3c5d2e7f1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'password_reset_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('token_hash', sa.String(length=64), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('used', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'ix_password_reset_tokens_token_hash',
        'password_reset_tokens',
        ['token_hash'],
        unique=True,
    )
    op.create_index(
        'ix_password_reset_tokens_user_id',
        'password_reset_tokens',
        ['user_id'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index('ix_password_reset_tokens_user_id', table_name='password_reset_tokens')
    op.drop_index('ix_password_reset_tokens_token_hash', table_name='password_reset_tokens')
    op.drop_table('password_reset_tokens')
