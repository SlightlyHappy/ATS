"""add section column to resume_chunks

Revision ID: 20250810_01
Revises: 20250810_00
Create Date: 2025-08-10

"""
from __future__ import annotations
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250810_01'
down_revision = '20250810_00'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # This migration is now a no-op since the section column 
    # is included in the initial schema (20250810_00)
    # This exists only for compatibility with existing deployments
    pass


def downgrade() -> None:
    # This migration is now a no-op since the section column 
    # is included in the initial schema (20250810_00)
    # This exists only for compatibility with existing deployments
    pass
