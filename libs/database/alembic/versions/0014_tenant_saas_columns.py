"""Add SaaS columns to tenant table

Revision ID: 0014_tenant_saas_columns
Revises: 0013_add_defect_tables
Create Date: 2026-02-23
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0014_tenant_saas_columns"
down_revision = "0013_add_defect_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tenant", sa.Column("domain", sa.String(), nullable=True))
    op.add_column("tenant", sa.Column("type", sa.String(), server_default="beauty", nullable=False))
    op.add_column("tenant", sa.Column("status", sa.String(), server_default="active", nullable=False))
    op.add_column("tenant", sa.Column("timezone", sa.String(), server_default="Asia/Jerusalem", nullable=False))
    op.add_column("tenant", sa.Column("theme_config", JSONB, server_default="{}", nullable=False))
    op.add_column("tenant", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))

    # Create unique index on domain (allows nulls)
    op.create_index("ix_tenant_domain", "tenant", ["domain"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_tenant_domain", table_name="tenant")
    op.drop_column("tenant", "updated_at")
    op.drop_column("tenant", "theme_config")
    op.drop_column("tenant", "timezone")
    op.drop_column("tenant", "status")
    op.drop_column("tenant", "type")
    op.drop_column("tenant", "domain")
