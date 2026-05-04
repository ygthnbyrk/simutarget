"""add paddle integration

Revision ID: b3a1f9d4c8e7
Revises: a9088355b259
Create Date: 2026-05-04 14:30:00.000000

Bu migration Paddle Billing entegrasyonu için gerekli alanları ekler:
- plans.paddle_price_id
- subscriptions.paddle_subscription_id, paddle_customer_id, paddle_transaction_id
- users.paddle_customer_id
- paddle_webhook_events tablosu (idempotency için)

NOT: Plans tablosundaki price_id'leri otomatik dolduruyoruz. Eğer plans
seed edilmediyse UPDATE etkisiz olur, sorun değil — manuel SQL ile
sonradan eklenebilir.
"""
from datetime import datetime

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b3a1f9d4c8e7'
down_revision = 'a9088355b259'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Plans tablosuna paddle_price_id ekle
    op.add_column(
        'plans',
        sa.Column('paddle_price_id', sa.String(length=100), nullable=True)
    )
    op.create_unique_constraint(
        'uq_plans_paddle_price_id',
        'plans',
        ['paddle_price_id']
    )
    op.create_index(
        'ix_plans_paddle_price_id',
        'plans',
        ['paddle_price_id']
    )

    # 2. Subscriptions tablosuna Paddle alanları ekle
    op.add_column(
        'subscriptions',
        sa.Column('paddle_subscription_id', sa.String(length=100), nullable=True)
    )
    op.add_column(
        'subscriptions',
        sa.Column('paddle_customer_id', sa.String(length=100), nullable=True)
    )
    op.add_column(
        'subscriptions',
        sa.Column('paddle_transaction_id', sa.String(length=100), nullable=True)
    )
    op.create_unique_constraint(
        'uq_subscriptions_paddle_subscription_id',
        'subscriptions',
        ['paddle_subscription_id']
    )
    op.create_index(
        'ix_subscriptions_paddle_subscription_id',
        'subscriptions',
        ['paddle_subscription_id']
    )
    op.create_index(
        'ix_subscriptions_paddle_customer_id',
        'subscriptions',
        ['paddle_customer_id']
    )
    op.create_index(
        'ix_subscriptions_paddle_transaction_id',
        'subscriptions',
        ['paddle_transaction_id']
    )

    # 3. Users tablosuna paddle_customer_id ekle
    op.add_column(
        'users',
        sa.Column('paddle_customer_id', sa.String(length=100), nullable=True)
    )
    op.create_index(
        'ix_users_paddle_customer_id',
        'users',
        ['paddle_customer_id']
    )

    # 4. paddle_webhook_events tablosu (idempotency için)
    op.create_table(
        'paddle_webhook_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.String(length=100), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('processing_error', sa.Text(), nullable=True),
        sa.Column('received_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('event_id', name='uq_paddle_webhook_events_event_id'),
    )
    op.create_index(
        'ix_paddle_webhook_events_event_id',
        'paddle_webhook_events',
        ['event_id']
    )
    op.create_index(
        'ix_paddle_webhook_events_event_type',
        'paddle_webhook_events',
        ['event_type']
    )

    # 5. Plan price_id'lerini doldur (Yiğit'in Paddle dashboard'da oluşturduğu price'lar)
    # Plans tablosu seed edilmediyse bu UPDATE'ler hiçbir row'u etkilemez, sorun değil.
    op.execute("""
        UPDATE plans SET paddle_price_id = 'pri_01kqs33hv52bkvb3nw05n56087' WHERE slug = 'disposable';
        UPDATE plans SET paddle_price_id = 'pri_01kqs34mta2bqd4kkzwmsjrp73' WHERE slug = 'starter';
        UPDATE plans SET paddle_price_id = 'pri_01kqs35fheh5zfh2dvc6fk74sj' WHERE slug = 'pro';
        UPDATE plans SET paddle_price_id = 'pri_01kqs3697tzy62tw22arqrzsq1' WHERE slug = 'business';
    """)


def downgrade():
    # paddle_webhook_events tablosunu kaldır
    op.drop_index('ix_paddle_webhook_events_event_type', table_name='paddle_webhook_events')
    op.drop_index('ix_paddle_webhook_events_event_id', table_name='paddle_webhook_events')
    op.drop_table('paddle_webhook_events')

    # users.paddle_customer_id
    op.drop_index('ix_users_paddle_customer_id', table_name='users')
    op.drop_column('users', 'paddle_customer_id')

    # subscriptions paddle alanları
    op.drop_index('ix_subscriptions_paddle_transaction_id', table_name='subscriptions')
    op.drop_index('ix_subscriptions_paddle_customer_id', table_name='subscriptions')
    op.drop_index('ix_subscriptions_paddle_subscription_id', table_name='subscriptions')
    op.drop_constraint('uq_subscriptions_paddle_subscription_id', 'subscriptions', type_='unique')
    op.drop_column('subscriptions', 'paddle_transaction_id')
    op.drop_column('subscriptions', 'paddle_customer_id')
    op.drop_column('subscriptions', 'paddle_subscription_id')

    # plans.paddle_price_id
    op.drop_index('ix_plans_paddle_price_id', table_name='plans')
    op.drop_constraint('uq_plans_paddle_price_id', 'plans', type_='unique')
    op.drop_column('plans', 'paddle_price_id')
