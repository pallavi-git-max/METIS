"""Remove lab_incharge role and workflow

Revision ID: remove_lab_incharge
Revises: 400a6aa65921
Create Date: 2025-10-11 17:44:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'remove_lab_incharge'
down_revision = '400a6aa65921'
branch_labels = None
depends_on = None


def upgrade():
    # First, update any existing lab_incharge_approved statuses to guide_approved
    # so they will be processed by HOD next
    op.execute("""
        UPDATE project_requests 
        SET status = 'guide_approved' 
        WHERE status = 'lab_incharge_approved'
    """)
    
    # Update any users with lab_incharge role to project_guide role
    op.execute("""
        UPDATE users 
        SET role = 'project_guide' 
        WHERE role = 'lab_incharge'
    """)
    
    # Now modify the tables
    with op.batch_alter_table('project_requests', schema=None) as batch_op:
        # Drop foreign key constraints first
        batch_op.drop_constraint('fk_project_requests_lab_incharge_approved_by', type_='foreignkey')
        
        # Drop the lab_incharge columns
        batch_op.drop_column('lab_incharge_approved_by')
        batch_op.drop_column('lab_incharge_approved_at')
        
        # Update the status enum to remove lab_incharge_approved
        batch_op.alter_column('status',
               existing_type=sa.Enum('pending', 'guide_approved', 'lab_incharge_approved', 'hod_approved', 'it_services_approved', 'approved', 'rejected', name='statusenum'),
               type_=sa.Enum('pending', 'guide_approved', 'hod_approved', 'it_services_approved', 'approved', 'rejected', name='statusenum'),
               existing_nullable=False)

    with op.batch_alter_table('users', schema=None) as batch_op:
        # Update the role enum to remove lab_incharge
        batch_op.alter_column('role',
               existing_type=sa.Enum('student', 'faculty', 'project_guide', 'lab_incharge', 'hod', 'it_services', 'admin', 'external', name='roleenum'),
               type_=sa.Enum('student', 'faculty', 'project_guide', 'hod', 'it_services', 'admin', 'external', name='roleenum'),
               existing_nullable=False)


def downgrade():
    # Reverse the changes - add back lab_incharge role and columns
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('role',
               existing_type=sa.Enum('student', 'faculty', 'project_guide', 'hod', 'it_services', 'admin', 'external', name='roleenum'),
               type_=sa.Enum('student', 'faculty', 'project_guide', 'lab_incharge', 'hod', 'it_services', 'admin', 'external', name='roleenum'),
               existing_nullable=False)

    with op.batch_alter_table('project_requests', schema=None) as batch_op:
        batch_op.alter_column('status',
               existing_type=sa.Enum('pending', 'guide_approved', 'hod_approved', 'it_services_approved', 'approved', 'rejected', name='statusenum'),
               type_=sa.Enum('pending', 'guide_approved', 'lab_incharge_approved', 'hod_approved', 'it_services_approved', 'approved', 'rejected', name='statusenum'),
               existing_nullable=False)
        
        batch_op.add_column(sa.Column('lab_incharge_approved_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('lab_incharge_approved_by', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_project_requests_lab_incharge_approved_by', 'users', ['lab_incharge_approved_by'], ['id'])
