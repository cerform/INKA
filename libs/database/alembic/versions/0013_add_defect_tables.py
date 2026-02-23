"""add defect tables

Revision ID: 0013
Revises: 0012
Create Date: 2026-02-22 10:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0013'
down_revision = '0012'
branch_labels = None
depends_on = None

def upgrade():
    # Enums
    op.execute("CREATE TYPE defectseverity AS ENUM ('S1', 'S2', 'S3', 'S4')")
    op.execute("CREATE TYPE defectstatus AS ENUM ('open', 'triaged', 'assigned', 'fixing', 'testing', 'resolved', 'closed', 'rejected')")
    op.execute("CREATE TYPE impactarea AS ENUM ('bot', 'backend', 'db', 'security', 'devops')")
    op.execute("CREATE TYPE detectedby AS ENUM ('user', 'qa', 'monitoring')")

    # defect_log
    op.create_table(
        'defect_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('environment', sa.String(), nullable=False),
        sa.Column('severity', sa.Enum('S1', 'S2', 'S3', 'S4', name='defectseverity'), nullable=False),
        sa.Column('impact_area', sa.Enum('bot', 'backend', 'db', 'security', 'devops', name='impactarea'), nullable=False),
        sa.Column('detected_by', sa.Enum('user', 'qa', 'monitoring', name='detectedby'), nullable=False),
        sa.Column('request_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('correlation_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('actor_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('open', 'triaged', 'assigned', 'fixing', 'testing', 'resolved', 'closed', 'rejected', name='defectstatus'), nullable=False),
        sa.Column('root_cause', sa.Text(), nullable=True),
        sa.Column('fix_commit_sha', sa.String(length=40), nullable=True),
        sa.Column('regression_test_added', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('assigned_agents', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('related_incidents', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('detected_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['actor_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_defect_log_severity'), 'defect_log', ['severity'], unique=False)
    op.create_index(op.f('ix_defect_log_status'), 'defect_log', ['status'], unique=False)
    op.create_index(op.f('ix_defect_log_request_id'), 'defect_log', ['request_id'], unique=False)

    # defect_event
    op.create_table(
        'defect_event',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('defect_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('actor_id', sa.Integer(), nullable=True),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['defect_id'], ['defect_log.id'], ),
        sa.ForeignKeyConstraint(['actor_id'], ['user.id'], ),

        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_defect_event_defect_id'), 'defect_event', ['defect_id'], unique=False)

def downgrade():
    op.drop_index(op.f('ix_defect_event_defect_id'), table_name='defect_event')
    op.drop_table('defect_event')
    op.drop_index(op.f('ix_defect_log_request_id'), table_name='defect_log')
    op.drop_index(op.f('ix_defect_log_status'), table_name='defect_log')
    op.drop_index(op.f('ix_defect_log_severity'), table_name='defect_log')
    op.drop_table('defect_log')
    op.execute("DROP TYPE detectedby")
    op.execute("DROP TYPE impactarea")
    op.execute("DROP TYPE defectstatus")
    op.execute("DROP TYPE defectseverity")
