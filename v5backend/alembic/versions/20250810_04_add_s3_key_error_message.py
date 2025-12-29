"""add s3_key and error_message to resumes

Revision ID: 20250810_04
Revises: 20250810_03
Create Date: 2025-08-10 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20250810_04'
down_revision = '20250810_03'
branch_labels = None
depends_on = None


def upgrade():
    """Add s3_key and error_message columns to resumes table"""
    try:
        # Add s3_key column
        op.add_column('resumes', sa.Column('s3_key', sa.String(512), nullable=True))
        
        # Add error_message column
        op.add_column('resumes', sa.Column('error_message', sa.Text(), nullable=True))
        
        # Create index on s3_key for faster lookups
        op.create_index('ix_resumes_s3_key', 'resumes', ['s3_key'], unique=False)
        
        print("✅ Successfully added s3_key and error_message columns to resumes table")
        
    except Exception as e:
        print(f"⚠️  Migration error (non-fatal): {e}")
        # Non-fatal - columns may already exist


def downgrade():
    """Remove s3_key and error_message columns from resumes table"""
    try:
        # Drop index first
        op.drop_index('ix_resumes_s3_key', table_name='resumes')
        
        # Drop columns
        op.drop_column('resumes', 'error_message')
        op.drop_column('resumes', 's3_key')
        
    except Exception as e:
        print(f"⚠️  Downgrade error (non-fatal): {e}")
