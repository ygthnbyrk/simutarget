"""add lemonsqueezy integration

Revision ID: c4f5e1a8d3b9
Revises: b3a1f9d4c8e7
Create Date: 2026-05-07 18:00:00.000000

Bu migration Lemon Squeezy entegrasyonu için gerekli alanları ekler:
- plans.lemonsqueezy_variant_id
- subscriptions.lemonsqueezy_subscription_id, lemonsqueezy_customer_id, lemonsqueezy_order_id
- users.lemonsqueezy_customer_id
- lemonsqueezy_webhook_events tablosu (idempotency için)

NOT: Paddle alanları SİLİNMEDİ — LS canlıya geçtikten sonra ayrı bir migration ile temizlenecek.
NOT: lemonsqueezy_variant_id seed'i otomatik yapılmıyor. Variant ID'leri Lemon Squeezy
dashboard'da product/variant oluşturulduktan sonra elle UPDATE ile gelir veya
Yiğit'in seed_plans script'i güncellenir. Şu an Plans seed edilmemiş olabilir,
UPDATE etkisiz olur — sorun değil.
"""
from datetime import datetime

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c4f5e1a8d3b9'
down_revision = 'b3a1f9d4c8e7'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Plans tablosuna lemonsqueezy_variant_id ekle
    op.add_column(
        'plans',
        sa.Column('lemonsqueezy_variant_id', sa.String(length=100), nullable=True)
    )
    op.create_unique_constraint(
        'uq_plans_lemonsqueezy_variant_id',
        'plans',
        ['lemonsqueezy_variant_id']
    )
    op.create_index(
        'ix_plans_lemonsqueezy_variant_id',
        'plans',
        ['lemonsqueezy_variant_id']
    )

    # 2. Subscriptions tablosuna Lemon Squeezy alanları ekle
    op.add_column(
        'subscriptions',
        sa.Column('lemonsqueezy_subscription_id', sa.String(length=100), nullable=True)
    )
    op.add_column(
        'subscriptions',
        sa.Column('lemonsqueezy_customer_id', sa.String(length=100), nullable=True)
    )
    op.add_column(
        'subscriptions',
        sa.Column('lemonsqueezy_order_id', sa.String(length=100), nullable=True)
    )
    op.create_unique_constraint(
        'uq_subscriptions_lemonsqueezy_subscription_id',
        'subscriptions',
        ['lemonsqueezy_subscription_id']
    )
    op.create_index(
        'ix_subscriptions_lemonsqueezy_subscription_id',
        'subscriptions',
        ['lemonsqueezy_subscription_id']
    )
    op.create_index(
        'ix_subscriptions_lemonsqueezy_customer_id',
        'subscriptions',
        ['lemonsqueezy_customer_id']
    )
    op.create_index(
        'ix_subscriptions_lemonsqueezy_order_id',
        'subscriptions',
        ['lemonsqueezy_order_id']
    )

    # 3. Users tablosuna lemonsqueezy_customer_id ekle
    op.add_column(
        'users',
        sa.Column('lemonsqueezy_customer_id', sa.String(length=100), nullable=True)
    )
    op.create_index(
        'ix_users_lemonsqueezy_customer_id',
        'users',
        ['lemonsqueezy_customer_id']
    )

    # 4. lemonsqueezy_webhook_events tablosu (idempotency için)
    # NOT: LS unique event_id göndermez. Backend raw_body'nin SHA256 hash'ini
    # event_id olarak kullanır. Aynı body 2 kez gelirse aynı hash → idempotency.
    op.create_table(
        'lemonsqueezy_webhook_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.String(length=100), nullable=False),  # SHA256 hex (64 char)
        sa.Column('event_name', sa.String(length=100), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('processing_error', sa.Text(), nullable=True),
        sa.Column('received_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('event_id', name='uq_lemonsqueezy_webhook_events_event_id'),
    )
    op.create_index(
        'ix_lemonsqueezy_webhook_events_event_id',
        'lemonsqueezy_webhook_events',
        ['event_id']
    )
    op.create_index(
        'ix_lemonsqueezy_webhook_events_event_name',
        'lemonsqueezy_webhook_events',
        ['event_name']
    )


def downgrade():
    # lemonsqueezy_webhook_events tablosunu kaldır
    op.drop_index('ix_lemonsqueezy_webhook_events_event_name', table_name='lemonsqueezy_webhook_events')
    op.drop_index('ix_lemonsqueezy_webhook_events_event_id', table_name='lemonsqueezy_webhook_events')
    op.drop_table('lemonsqueezy_webhook_events')

    # users.lemonsqueezy_customer_id
    op.drop_index('ix_users_lemonsqueezy_customer_id', table_name='users')
    op.drop_column('users', 'lemonsqueezy_customer_id')

    # subscriptions LS alanları
    op.drop_index('ix_subscriptions_lemonsqueezy_order_id', table_name='subscriptions')
    op.drop_index('ix_subscriptions_lemonsqueezy_customer_id', table_name='subscriptions')
    op.drop_index('ix_subscriptions_lemonsqueezy_subscription_id', table_name='subscriptions')
    op.drop_constraint('uq_subscriptions_lemonsqueezy_subscription_id', 'subscriptions', type_='unique')
    op.drop_column('subscriptions', 'lemonsqueezy_order_id')
    op.drop_column('subscriptions', 'lemonsqueezy_customer_id')
    op.drop_column('subscriptions', 'lemonsqueezy_subscription_id')

    # plans.lemonsqueezy_variant_id
    op.drop_index('ix_plans_lemonsqueezy_variant_id', table_name='plans')
    op.drop_constraint('uq_plans_lemonsqueezy_variant_id', 'plans', type_='unique')
    op.drop_column('plans', 'lemonsqueezy_variant_id')
