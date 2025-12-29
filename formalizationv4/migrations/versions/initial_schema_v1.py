"""Initial database schema with all tables

Revision ID: initial_schema_v1
Revises: 
Create Date: 2025-08-05 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = 'initial_schema_v1'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create users table
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('email', sa.String(length=120), nullable=False),
        sa.Column('username', sa.String(length=80), nullable=True),
        sa.Column('password_hash', sa.String(length=128), nullable=True),
        sa.Column('first_name', sa.String(length=50), nullable=False),
        sa.Column('last_name', sa.String(length=50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('is_admin', sa.Boolean(), nullable=True, default=False),
        sa.Column('credits_balance', sa.Integer(), nullable=True, default=10),
        sa.Column('total_credits_purchased', sa.Integer(), nullable=True, default=0),
        sa.Column('total_credits_used', sa.Integer(), nullable=True, default=0),
        sa.Column('last_credit_transaction', sa.DateTime(), nullable=True),
        sa.Column('subscription_tier', sa.String(length=20), nullable=True, default='free'),
        sa.Column('subscription_expires', sa.DateTime(), nullable=True),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.Column('failed_login_attempts', sa.Integer(), nullable=True, default=0),
        sa.Column('account_locked_until', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_users_email', 'users', ['email'], unique=True)
    op.create_index('idx_users_username', 'users', ['username'], unique=True)

    # Create credit_transactions table
    op.create_table('credit_transactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('transaction_type', sa.String(length=50), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('balance_after', sa.Integer(), nullable=False),
        sa.Column('reference_id', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')
    )
    op.create_index('idx_credit_transactions_user_id', 'credit_transactions', ['user_id'])
    op.create_index('idx_credit_transactions_type', 'credit_transactions', ['transaction_type'])

    # Create resumes table
    op.create_table('resumes',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('file_type', sa.String(length=50), nullable=True),
        sa.Column('processed_text', sa.Text(), nullable=True),
        sa.Column('processing_status', sa.String(length=50), nullable=True, default='pending'),
        sa.Column('processing_error', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')
    )
    op.create_index('idx_resumes_user_id', 'resumes', ['user_id'])
    op.create_index('idx_resumes_status', 'resumes', ['processing_status'])

    # Create analyses table
    op.create_table('analyses',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('resume_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('analysis_type', sa.String(length=50), nullable=False, default='comprehensive'),
        sa.Column('status', sa.String(length=50), nullable=False, default='pending'),
        sa.Column('progress', sa.Integer(), nullable=True, default=0),
        sa.Column('result', postgresql.JSONB(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('processing_time', sa.Float(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')
    )
    op.create_index('idx_analyses_resume_id', 'analyses', ['resume_id'])
    op.create_index('idx_analyses_user_id', 'analyses', ['user_id'])
    op.create_index('idx_analyses_status', 'analyses', ['status'])

    # Create analysis_queue table
    op.create_table('analysis_queue',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('resume_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=True, default=1),
        sa.Column('status', sa.String(length=50), nullable=False, default='queued'),
        sa.Column('attempts', sa.Integer(), nullable=True, default=0),
        sa.Column('max_attempts', sa.Integer(), nullable=True, default=3),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('estimated_completion', sa.DateTime(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')
    )
    op.create_index('idx_analysis_queue_status', 'analysis_queue', ['status'])
    op.create_index('idx_analysis_queue_priority', 'analysis_queue', ['priority'])

    # Create batch_uploads table
    op.create_table('batch_uploads',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('batch_name', sa.String(length=200), nullable=False),
        sa.Column('total_files', sa.Integer(), nullable=False),
        sa.Column('processed_files', sa.Integer(), nullable=True, default=0),
        sa.Column('failed_files', sa.Integer(), nullable=True, default=0),
        sa.Column('status', sa.String(length=50), nullable=False, default='processing'),
        sa.Column('file_paths', postgresql.JSONB(), nullable=True),
        sa.Column('processing_summary', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')
    )
    op.create_index('idx_batch_uploads_user_id', 'batch_uploads', ['user_id'])
    op.create_index('idx_batch_uploads_status', 'batch_uploads', ['status'])


def downgrade():
    op.drop_table('batch_uploads')
    op.drop_table('analysis_queue')
    op.drop_table('analyses')
    op.drop_table('resumes')
    op.drop_table('credit_transactions')
    op.drop_table('users')
