"""create_all_tables

Revision ID: d1d1df2793c4
Revises: 
Create Date: 2025-02-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

# revision identifiers, used by Alembic.
revision: str = 'd1d1df2793c4'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Plans tablosu
    op.create_table('plans',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('slug', sa.String(50), unique=True, nullable=False),
        sa.Column('track', sa.String(20), nullable=False),  # individual / agency
        sa.Column('price_monthly', sa.Numeric(10, 2), nullable=False),
        sa.Column('credits_monthly', sa.Integer(), nullable=False),
        sa.Column('max_team_size', sa.Integer(), default=1),
        sa.Column('features', JSON, nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # 2. Teams tablosu
    op.create_table('teams',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('max_members', sa.Integer(), default=1),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # 3. Users tablosu
    op.create_table('users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('role', sa.String(20), default='user'),  # user / admin
        sa.Column('team_id', sa.Integer(), sa.ForeignKey('teams.id'), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # 4. Subscriptions tablosu
    op.create_table('subscriptions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('plan_id', sa.Integer(), sa.ForeignKey('plans.id'), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),  # active / cancelled / past_due
        sa.Column('stripe_subscription_id', sa.String(255), nullable=True),
        sa.Column('current_period_start', sa.DateTime(), nullable=False),
        sa.Column('current_period_end', sa.DateTime(), nullable=False),
        sa.Column('cancel_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # 5. Credit Ledger tablosu
    op.create_table('credit_ledger',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),  # + veya -
        sa.Column('type', sa.String(20), nullable=False),  # grant / usage / topup / expire
        sa.Column('balance_after', sa.Integer(), nullable=False),
        sa.Column('reference_id', sa.String(255), nullable=True),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # 6. Campaigns tablosu
    op.create_table('campaigns',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('type', sa.String(20), nullable=False),  # single / ab / abc
        sa.Column('content', JSON, nullable=False),
        sa.Column('persona_count', sa.Integer(), nullable=False),
        sa.Column('region', sa.String(10), nullable=False),  # TR / US / EU / MENA
        sa.Column('filters', JSON, nullable=True),
        sa.Column('status', sa.String(20), default='pending'),  # pending / running / completed / failed
        sa.Column('results', JSON, nullable=True),
        sa.Column('credits_consumed', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # 7. Campaign Persona Responses tablosu
    op.create_table('campaign_persona_responses',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('campaign_id', sa.Integer(), sa.ForeignKey('campaigns.id'), nullable=False),
        sa.Column('persona_data', JSON, nullable=False),
        sa.Column('decision', sa.String(10), nullable=False),  # EVET / HAYIR
        sa.Column('confidence', sa.Integer(), nullable=False),  # 1-10
        sa.Column('reasoning', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # 8. Usage Logs tablosu
    op.create_table('usage_logs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('campaign_id', sa.Integer(), sa.ForeignKey('campaigns.id'), nullable=True),
        sa.Column('persona_count', sa.Integer(), nullable=False),
        sa.Column('credits_used', sa.Integer(), nullable=False),
        sa.Column('region', sa.String(10), nullable=True),
        sa.Column('filters_used', JSON, nullable=True),
        sa.Column('response_time_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # İndeksler
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_index('ix_credit_ledger_user_id', 'credit_ledger', ['user_id'])
    op.create_index('ix_credit_ledger_type', 'credit_ledger', ['type'])
    op.create_index('ix_campaigns_user_id', 'campaigns', ['user_id'])
    op.create_index('ix_usage_logs_user_id', 'usage_logs', ['user_id'])
    op.create_index('ix_subscriptions_user_id', 'subscriptions', ['user_id'])


def downgrade() -> None:
    op.drop_table('usage_logs')
    op.drop_table('campaign_persona_responses')
    op.drop_table('campaigns')
    op.drop_table('credit_ledger')
    op.drop_table('subscriptions')
    op.drop_table('users')
    op.drop_table('teams')
    op.drop_table('plans')