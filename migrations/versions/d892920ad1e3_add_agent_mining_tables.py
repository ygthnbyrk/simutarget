"""add_agent_mining_tables

Revision ID: d892920ad1e3
Revises: d1d1df2793c4
Create Date: 2026-03-10 22:31:14.027354

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd892920ad1e3'
down_revision: Union[str, Sequence[str], None] = 'd1d1df2793c4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('am_personas',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('segment', sa.Enum('TR', 'GLOBAL', name='segmenttype'), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('age', sa.Integer(), nullable=False),
    sa.Column('gender', sa.String(length=20), nullable=False),
    sa.Column('city', sa.String(length=100), nullable=False),
    sa.Column('country', sa.String(length=100), nullable=False),
    sa.Column('income_level', sa.String(length=30), nullable=False),
    sa.Column('education', sa.String(length=50), nullable=False),
    sa.Column('occupation', sa.String(length=100), nullable=False),
    sa.Column('marital_status', sa.String(length=30), nullable=False),
    sa.Column('household_size', sa.Integer(), nullable=True),
    sa.Column('openness', sa.Float(), nullable=False),
    sa.Column('conscientiousness', sa.Float(), nullable=False),
    sa.Column('extraversion', sa.Float(), nullable=False),
    sa.Column('agreeableness', sa.Float(), nullable=False),
    sa.Column('neuroticism', sa.Float(), nullable=False),
    sa.Column('values', sa.JSON(), nullable=False),
    sa.Column('interests', sa.JSON(), nullable=False),
    sa.Column('brands_liked', sa.JSON(), nullable=False),
    sa.Column('price_sensitivity', sa.Float(), nullable=False),
    sa.Column('social_media_usage', sa.String(length=20), nullable=True),
    sa.Column('online_shopping_freq', sa.String(length=20), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('generation_model', sa.String(length=50), nullable=True),
    sa.Column('is_validated', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_am_personas_segment'), 'am_personas', ['segment'], unique=False)
    op.create_table('am_reference_campaigns',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('category', sa.String(length=100), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('product_name', sa.String(length=200), nullable=True),
    sa.Column('price_tl', sa.Float(), nullable=True),
    sa.Column('price_usd', sa.Float(), nullable=True),
    sa.Column('target_segment', sa.Enum('TR', 'GLOBAL', name='segmenttype'), nullable=True),
    sa.Column('target_age_min', sa.Integer(), nullable=True),
    sa.Column('target_age_max', sa.Integer(), nullable=True),
    sa.Column('status', sa.Enum('PENDING', 'RUNNING', 'COMPLETED', 'FAILED', name='campaignstatus'), nullable=False),
    sa.Column('total_personas_run', sa.Integer(), nullable=True),
    sa.Column('buy_count', sa.Integer(), nullable=True),
    sa.Column('no_buy_count', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('completed_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('am_agent_decisions',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('persona_id', sa.UUID(), nullable=False),
    sa.Column('campaign_id', sa.UUID(), nullable=False),
    sa.Column('decision', sa.Enum('BUY', 'NO_BUY', name='decisiontype'), nullable=False),
    sa.Column('confidence', sa.Integer(), nullable=False),
    sa.Column('reasoning', sa.Text(), nullable=True),
    sa.Column('system_prompt_hash', sa.String(length=64), nullable=True),
    sa.Column('input_tokens', sa.Integer(), nullable=True),
    sa.Column('output_tokens', sa.Integer(), nullable=True),
    sa.Column('model_used', sa.String(length=50), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['campaign_id'], ['am_reference_campaigns.id'], ),
    sa.ForeignKeyConstraint(['persona_id'], ['am_personas.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_am_agent_decisions_campaign_id'), 'am_agent_decisions', ['campaign_id'], unique=False)
    op.create_index(op.f('ix_am_agent_decisions_decision'), 'am_agent_decisions', ['decision'], unique=False)
    op.create_index(op.f('ix_am_agent_decisions_persona_id'), 'am_agent_decisions', ['persona_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_am_agent_decisions_persona_id'), table_name='am_agent_decisions')
    op.drop_index(op.f('ix_am_agent_decisions_decision'), table_name='am_agent_decisions')
    op.drop_index(op.f('ix_am_agent_decisions_campaign_id'), table_name='am_agent_decisions')
    op.drop_table('am_agent_decisions')
    op.drop_table('am_reference_campaigns')
    op.drop_index(op.f('ix_am_personas_segment'), table_name='am_personas')
    op.drop_table('am_personas')