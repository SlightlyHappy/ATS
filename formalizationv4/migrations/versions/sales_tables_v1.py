"""Add sales intelligence tables

Revision ID: sales_tables_v1
Revises: admin_system_v1
Create Date: 2025-08-05 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = 'sales_tables_v1'
down_revision = 'admin_system_v1'
branch_labels = None
depends_on = None


def upgrade():
    # Create leads table
    op.create_table('leads',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('company_name', sa.String(length=200), nullable=False),
        sa.Column('contact_person', sa.String(length=100), nullable=True),
        sa.Column('email', sa.String(length=120), nullable=True),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('industry', sa.String(length=100), nullable=True),
        sa.Column('company_size', sa.String(length=50), nullable=True),
        sa.Column('location', sa.String(length=100), nullable=True),
        sa.Column('website', sa.String(length=200), nullable=True),
        sa.Column('source', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, default='new'),
        sa.Column('priority', sa.String(length=20), nullable=False, default='medium'),
        sa.Column('score', sa.Float(), nullable=True, default=0.0),
        sa.Column('estimated_value', sa.Float(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('tags', postgresql.JSONB(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('assigned_to', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('last_contact', sa.DateTime(), nullable=True),
        sa.Column('next_followup', sa.DateTime(), nullable=True),
        sa.Column('conversion_date', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['assigned_to'], ['users.id'], ondelete='SET NULL')
    )
    op.create_index('idx_leads_status', 'leads', ['status'])
    op.create_index('idx_leads_priority', 'leads', ['priority'])
    op.create_index('idx_leads_score', 'leads', ['score'])
    op.create_index('idx_leads_assigned_to', 'leads', ['assigned_to'])

    # Create lead_score_history table
    op.create_table('lead_score_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('lead_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('previous_score', sa.Float(), nullable=True),
        sa.Column('new_score', sa.Float(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], ondelete='CASCADE')
    )
    op.create_index('idx_lead_score_history_lead_id', 'lead_score_history', ['lead_id'])

    # Create lead_activities table
    op.create_table('lead_activities',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('lead_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('activity_type', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('performed_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['performed_by'], ['users.id'], ondelete='SET NULL')
    )
    op.create_index('idx_lead_activities_lead_id', 'lead_activities', ['lead_id'])
    op.create_index('idx_lead_activities_type', 'lead_activities', ['activity_type'])

    # Create sales_metrics table
    op.create_table('sales_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('metric_date', sa.Date(), nullable=False),
        sa.Column('new_leads', sa.Integer(), nullable=True, default=0),
        sa.Column('qualified_leads', sa.Integer(), nullable=True, default=0),
        sa.Column('converted_leads', sa.Integer(), nullable=True, default=0),
        sa.Column('total_revenue', sa.Float(), nullable=True, default=0.0),
        sa.Column('average_deal_size', sa.Float(), nullable=True, default=0.0),
        sa.Column('conversion_rate', sa.Float(), nullable=True, default=0.0),
        sa.Column('pipeline_value', sa.Float(), nullable=True, default=0.0),
        sa.Column('activities_completed', sa.Integer(), nullable=True, default=0),
        sa.Column('response_rate', sa.Float(), nullable=True, default=0.0),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_sales_metrics_date', 'sales_metrics', ['metric_date'], unique=True)

    # Create roi_calculations table
    op.create_table('roi_calculations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('lead_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('calculation_date', sa.DateTime(), nullable=False),
        sa.Column('investment_amount', sa.Float(), nullable=False),
        sa.Column('expected_return', sa.Float(), nullable=False),
        sa.Column('actual_return', sa.Float(), nullable=True),
        sa.Column('roi_percentage', sa.Float(), nullable=False),
        sa.Column('payback_period_months', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('calculated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['calculated_by'], ['users.id'], ondelete='SET NULL')
    )
    op.create_index('idx_roi_calculations_lead_id', 'roi_calculations', ['lead_id'])


def downgrade():
    op.drop_table('roi_calculations')
    op.drop_table('sales_metrics')
    op.drop_table('lead_activities')
    op.drop_table('lead_score_history')
    op.drop_table('leads')
