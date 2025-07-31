"""Add tender tables

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create tender_projects table
    op.create_table('tender_projects',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('project_name', sa.String(), nullable=False),
        sa.Column('source_file_id', sa.Integer(), nullable=True),
        sa.Column('source_filename', sa.String(), nullable=True),
        sa.Column('status', sa.Enum('CREATED', 'ANALYZING', 'ANALYZED', 'OUTLINING', 'OUTLINED', 'GENERATING', 'GENERATED', 'EXPORTING', 'COMPLETED', 'FAILED', name='tenderstatus'), nullable=False),
        sa.Column('progress', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('ix_tender_projects_tenant_id', 'tender_projects', ['tenant_id'])
    op.create_index('ix_tender_projects_user_id', 'tender_projects', ['user_id'])
    op.create_index('ix_tender_projects_status', 'tender_projects', ['status'])
    op.create_index('ix_tender_projects_created_at', 'tender_projects', ['created_at'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_tender_projects_created_at', table_name='tender_projects')
    op.drop_index('ix_tender_projects_status', table_name='tender_projects')
    op.drop_index('ix_tender_projects_user_id', table_name='tender_projects')
    op.drop_index('ix_tender_projects_tenant_id', table_name='tender_projects')
    
    # Drop table
    op.drop_table('tender_projects')
    
    # Drop enum type (for PostgreSQL)
    # For SQLite, this is not needed as it doesn't have native enum support