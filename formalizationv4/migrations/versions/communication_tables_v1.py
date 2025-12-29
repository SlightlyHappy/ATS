"""Add communication and HR templates tables

Revision ID: communication_tables_v1
Revises: analytics_tables_v1
Create Date: 2025-08-05 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = 'communication_tables_v1'
down_revision = 'analytics_tables_v1'
branch_labels = None
depends_on = None


def upgrade():
    # Create hr_templates table
    op.create_table('hr_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=300), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('subject_template', sa.String(length=500), nullable=True),
        sa.Column('variables', postgresql.JSONB(), nullable=True),
        sa.Column('legal_compliance_tags', postgresql.JSONB(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_default', sa.Boolean(), nullable=False, default=False),
        sa.Column('usage_count', sa.Integer(), nullable=True, default=0),
        sa.Column('version', sa.String(length=20), nullable=True, default='1.0'),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('tags', postgresql.JSONB(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ondelete='SET NULL')
    )
    op.create_index('idx_hr_templates_name', 'hr_templates', ['name'])
    op.create_index('idx_hr_templates_category', 'hr_templates', ['category'])
    op.create_index('idx_hr_templates_type', 'hr_templates', ['type'])
    op.create_index('idx_hr_templates_is_active', 'hr_templates', ['is_active'])

    # Create template_generations table
    op.create_table('template_generations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('template_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('candidate_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('generated_subject', sa.String(length=500), nullable=True),
        sa.Column('generated_content', sa.Text(), nullable=False),
        sa.Column('variables_used', postgresql.JSONB(), nullable=True),
        sa.Column('generation_context', postgresql.JSONB(), nullable=True),
        sa.Column('delivery_method', sa.String(length=50), nullable=True),
        sa.Column('delivery_status', sa.String(length=50), nullable=True, default='draft'),
        sa.Column('delivered_at', sa.DateTime(), nullable=True),
        sa.Column('opened_at', sa.DateTime(), nullable=True),
        sa.Column('clicked_at', sa.DateTime(), nullable=True),
        sa.Column('response_received_at', sa.DateTime(), nullable=True),
        sa.Column('feedback_rating', sa.Integer(), nullable=True),
        sa.Column('feedback_notes', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['template_id'], ['hr_templates.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['candidate_id'], ['candidates.id'], ondelete='SET NULL')
    )
    op.create_index('idx_template_generations_template_id', 'template_generations', ['template_id'])
    op.create_index('idx_template_generations_user_id', 'template_generations', ['user_id'])
    op.create_index('idx_template_generations_candidate_id', 'template_generations', ['candidate_id'])
    op.create_index('idx_template_generations_delivery_status', 'template_generations', ['delivery_status'])

    # Create compliance_rules table
    op.create_table('compliance_rules',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('rule_type', sa.String(length=50), nullable=False),
        sa.Column('scope', sa.String(length=100), nullable=False),
        sa.Column('conditions', postgresql.JSONB(), nullable=False),
        sa.Column('actions', postgresql.JSONB(), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False, default='medium'),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_mandatory', sa.Boolean(), nullable=False, default=False),
        sa.Column('legal_reference', sa.Text(), nullable=True),
        sa.Column('applicable_regions', postgresql.JSONB(), nullable=True),
        sa.Column('applicable_industries', postgresql.JSONB(), nullable=True),
        sa.Column('version', sa.String(length=20), nullable=True, default='1.0'),
        sa.Column('effective_from', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ondelete='SET NULL')
    )
    op.create_index('idx_compliance_rules_name', 'compliance_rules', ['name'])
    op.create_index('idx_compliance_rules_category', 'compliance_rules', ['category'])
    op.create_index('idx_compliance_rules_type', 'compliance_rules', ['rule_type'])
    op.create_index('idx_compliance_rules_is_active', 'compliance_rules', ['is_active'])


def downgrade():
    op.drop_table('compliance_rules')
    op.drop_table('template_generations')
    op.drop_table('hr_templates')
