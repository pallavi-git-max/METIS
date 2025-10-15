"""Add closed status to requests

Revision ID: add_closed_status
Revises: remove_lab_incharge
Create Date: 2025-10-14 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_closed_status'
down_revision = 'remove_lab_incharge'
branch_labels = None
depends_on = None


def upgrade():
    # Add closed_at and closed_by columns
    with op.batch_alter_table('project_requests', schema=None) as batch_op:
        batch_op.add_column(sa.Column('closed_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('closed_by', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_project_requests_closed_by', 'users', ['closed_by'], ['id'])
        
        # Update the status enum to include 'closed'
        batch_op.alter_column('status',
               existing_type=sa.Enum('pending', 'guide_approved', 'hod_approved', 'it_services_approved', 'approved', 'rejected', name='statusenum'),
               type_=sa.Enum('pending', 'guide_approved', 'hod_approved', 'it_services_approved', 'approved', 'rejected', 'closed', name='statusenum'),
               existing_nullable=False)


def downgrade():
    # Remove closed status and columns
    with op.batch_alter_table('project_requests', schema=None) as batch_op:
        batch_op.alter_column('status',
               existing_type=sa.Enum('pending', 'guide_approved', 'hod_approved', 'it_services_approved', 'approved', 'rejected', 'closed', name='statusenum'),
               type_=sa.Enum('pending', 'guide_approved', 'hod_approved', 'it_services_approved', 'approved', 'rejected', name='statusenum'),
               existing_nullable=False)
        
        batch_op.drop_constraint('fk_project_requests_closed_by', type_='foreignkey')
        batch_op.drop_column('closed_by')
        batch_op.drop_column('closed_at')
