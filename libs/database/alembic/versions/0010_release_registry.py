"""Release registry migration

Revision ID: 0010_release_registry
Revises: (previous migration id)
Create Date: 2026-02-22
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "0010_release_registry"
down_revision = None   # Set to your last migration revision ID
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "release_registry",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("version", sa.String(20), nullable=False),
        sa.Column("environment", sa.String(10), nullable=False),
        sa.Column("git_sha", sa.CHAR(40), nullable=False),
        sa.Column("git_tag", sa.String(50), nullable=True),
        sa.Column("docker_digest", sa.Text, nullable=True),
        sa.Column("sbom_url", sa.Text, nullable=True),
        sa.Column("coverage_report_url", sa.Text, nullable=True),
        sa.Column("vuln_report_url", sa.Text, nullable=True),
        sa.Column("changelog_url", sa.Text, nullable=True),
        sa.Column("deployed_by", sa.String(100), nullable=False),
        sa.Column(
            "deployed_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("rollback_revision", sa.String(200), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="DEPLOYED"),
        sa.Column("rolled_back_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("rolled_back_reason", sa.Text, nullable=True),
        sa.Column("gate_checklist", JSONB, nullable=True),
        sa.Column("is_canary", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("canary_percent", sa.SmallInteger, nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        # Constraints
        sa.CheckConstraint(
            "environment IN ('dev', 'stage', 'prod')",
            name="ck_rr_environment"
        ),
        sa.CheckConstraint(
            "status IN ('DEPLOYED','ROLLED_BACK','SUPERSEDED')",
            name="ck_rr_status"
        ),
        sa.CheckConstraint(
            "canary_percent BETWEEN 0 AND 100",
            name="ck_rr_canary_percent"
        ),
    )
    op.create_index("idx_rr_env_version", "release_registry", ["environment", "version"])
    op.create_index("idx_rr_status", "release_registry", ["status"])
    op.create_index(
        "idx_rr_deployed_at",
        "release_registry",
        [sa.text("deployed_at DESC")],
    )


def downgrade() -> None:
    op.drop_index("idx_rr_deployed_at", table_name="release_registry")
    op.drop_index("idx_rr_status", table_name="release_registry")
    op.drop_index("idx_rr_env_version", table_name="release_registry")
    op.drop_table("release_registry")
