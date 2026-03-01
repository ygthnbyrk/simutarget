# backend/alembic/versions/add_google_oauth_fields.py
"""Add Google OAuth fields to users table

Revision ID: add_google_oauth
Revises: (previous migration)
Create Date: 2025-01-28
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'add_google_oauth'
down_revision = None  # Önceki migration ID'sini buraya ekle
branch_labels = None
depends_on = None

def upgrade():
    # Google OAuth alanlarını ekle
    op.add_column('users', sa.Column('google_id', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('profile_picture', sa.String(500), nullable=True))
    
    # google_id için unique index
    op.create_index('ix_users_google_id', 'users', ['google_id'], unique=True)
    
    # password_hash'i nullable yap (Google-only kullanıcılar için)
    op.alter_column('users', 'password_hash',
                    existing_type=sa.String(255),
                    nullable=True)

def downgrade():
    op.drop_index('ix_users_google_id', table_name='users')
    op.drop_column('users', 'profile_picture')
    op.drop_column('users', 'google_id')
    op.alter_column('users', 'password_hash',
                    existing_type=sa.String(255),
                    nullable=False)
