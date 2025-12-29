"""Add candidate management tables

Revision ID: candidate_tables_v1
Revises: sales_tables_v1
Create Date: 2025-08-05 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = 'candidate_tables_v1'
down_revision = 'sales_tables_v1'
branch_labels = None
depends_on = None


def upgrade():
    # Create candidates table
    op.create_table('candidates',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=120), nullable=False),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('current_position', sa.String(length=200), nullable=True),
        sa.Column('current_company', sa.String(length=200), nullable=True),
        sa.Column('experience_years', sa.Float(), nullable=True),
        sa.Column('skills', postgresql.JSONB(), nullable=True),
        sa.Column('education', postgresql.JSONB(), nullable=True),
        sa.Column('location', sa.String(length=100), nullable=True),
        sa.Column('preferred_locations', postgresql.JSONB(), nullable=True),
        sa.Column('salary_expectation', sa.Float(), nullable=True),
        sa.Column('availability_date', sa.Date(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, default='active'),
        sa.Column('stage', sa.String(length=50), nullable=False, default='sourced'),
        sa.Column('source', sa.String(length=100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('tags', postgresql.JSONB(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('assigned_recruiter', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['assigned_recruiter'], ['users.id'], ondelete='SET NULL')
    )
    op.create_index('idx_candidates_email', 'candidates', ['email'], unique=True)
    op.create_index('idx_candidates_status', 'candidates', ['status'])
    op.create_index('idx_candidates_stage', 'candidates', ['stage'])
    op.create_index('idx_candidates_recruiter', 'candidates', ['assigned_recruiter'])

    # Create candidate_activities table
    op.create_table('candidate_activities',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('candidate_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('activity_type', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('outcome', sa.String(length=100), nullable=True),
        sa.Column('scheduled_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('performed_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['candidate_id'], ['candidates.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['performed_by'], ['users.id'], ondelete='SET NULL')
    )
    op.create_index('idx_candidate_activities_candidate_id', 'candidate_activities', ['candidate_id'])
    op.create_index('idx_candidate_activities_type', 'candidate_activities', ['activity_type'])

    # Create pipeline_stage_history table
    op.create_table('pipeline_stage_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('candidate_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('from_stage', sa.String(length=50), nullable=True),
        sa.Column('to_stage', sa.String(length=50), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('moved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('moved_at', sa.DateTime(), nullable=True, default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['candidate_id'], ['candidates.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['moved_by'], ['users.id'], ondelete='SET NULL')
    )
    op.create_index('idx_pipeline_stage_history_candidate_id', 'pipeline_stage_history', ['candidate_id'])

    # Create interviews table
    op.create_table('interviews',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('candidate_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('interviewer_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('round_number', sa.Integer(), nullable=False, default=1),
        sa.Column('interview_type', sa.String(length=50), nullable=False),
        sa.Column('scheduled_at', sa.DateTime(), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=True, default=60),
        sa.Column('location', sa.String(length=200), nullable=True),
        sa.Column('meeting_link', sa.String(length=500), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, default='scheduled'),
        sa.Column('feedback', sa.Text(), nullable=True),
        sa.Column('rating', sa.Integer(), nullable=True),
        sa.Column('recommendation', sa.String(length=50), nullable=True),
        sa.Column('technical_score', sa.Float(), nullable=True),
        sa.Column('communication_score', sa.Float(), nullable=True),
        sa.Column('cultural_fit_score', sa.Float(), nullable=True),
        sa.Column('overall_score', sa.Float(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['candidate_id'], ['candidates.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['interviewer_id'], ['users.id'], ondelete='SET NULL')
    )
    op.create_index('idx_interviews_candidate_id', 'interviews', ['candidate_id'])
    op.create_index('idx_interviews_interviewer_id', 'interviews', ['interviewer_id'])
    op.create_index('idx_interviews_scheduled_at', 'interviews', ['scheduled_at'])

    # Create candidate_alerts table
    op.create_table('candidate_alerts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('candidate_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('alert_type', sa.String(length=50), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False, default='info'),
        sa.Column('is_read', sa.Boolean(), nullable=False, default=False),
        sa.Column('target_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['candidate_id'], ['candidates.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_user_id'], ['users.id'], ondelete='SET NULL')
    )
    op.create_index('idx_candidate_alerts_candidate_id', 'candidate_alerts', ['candidate_id'])
    op.create_index('idx_candidate_alerts_target_user', 'candidate_alerts', ['target_user_id'])

    # Create hiring_analytics table
    op.create_table('hiring_analytics',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('analytics_date', sa.Date(), nullable=False),
        sa.Column('total_candidates', sa.Integer(), nullable=True, default=0),
        sa.Column('new_candidates', sa.Integer(), nullable=True, default=0),
        sa.Column('sourced_candidates', sa.Integer(), nullable=True, default=0),
        sa.Column('screened_candidates', sa.Integer(), nullable=True, default=0),
        sa.Column('interviewed_candidates', sa.Integer(), nullable=True, default=0),
        sa.Column('hired_candidates', sa.Integer(), nullable=True, default=0),
        sa.Column('rejected_candidates', sa.Integer(), nullable=True, default=0),
        sa.Column('time_to_hire_avg_days', sa.Float(), nullable=True),
        sa.Column('source_effectiveness', postgresql.JSONB(), nullable=True),
        sa.Column('stage_conversion_rates', postgresql.JSONB(), nullable=True),
        sa.Column('quality_metrics', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_hiring_analytics_date', 'hiring_analytics', ['analytics_date'], unique=True)


def downgrade():
    op.drop_table('hiring_analytics')
    op.drop_table('candidate_alerts')
    op.drop_table('interviews')
    op.drop_table('pipeline_stage_history')
    op.drop_table('candidate_activities')
    op.drop_table('candidates')
