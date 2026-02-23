"""Implement Salon availability and Inventory models

Revision ID: 0012_salon_inventory
Revises: 0011_multi_tenancy
Create Date: 2026-02-22
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0012_salon_inventory"
down_revision = "0011_multi_tenancy"
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Salon Availability
    op.create_table(
        "salon_working_hours",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenant.id"), nullable=False, index=True),
        sa.Column("day_of_week", sa.Integer(), nullable=False),
        sa.Column("open_time", sa.Time(), nullable=False),
        sa.Column("close_time", sa.Time(), nullable=False),
        sa.Column("is_closed", sa.Boolean(), server_default='false', nullable=False),
    )
    op.create_table(
        "salon_closed_day",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenant.id"), nullable=False, index=True),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("reason", sa.String(), nullable=True),
    )

    # 2. Inventory
    op.create_table(
        "material",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenant.id"), nullable=False, index=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("unit", sa.String(), nullable=False),
        sa.Column("stock_quantity", sa.Numeric(precision=10, scale=2), server_default='0', nullable=False),
        sa.Column("reorder_threshold", sa.Numeric(precision=10, scale=2), server_default='10', nullable=False),
    )
    op.create_table(
        "stock_entry",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenant.id"), nullable=False, index=True),
        sa.Column("material_id", sa.Integer(), sa.ForeignKey("material.id"), nullable=False),
        sa.Column("booking_id", sa.Integer(), sa.ForeignKey("booking.id"), nullable=True),
        sa.Column("delta", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("reason", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_table(
        "purchase_order",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenant.id"), nullable=False, index=True),
        sa.Column("material_id", sa.Integer(), sa.ForeignKey("material.id"), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("status", sa.String(), server_default='ordered', nullable=False),
        sa.Column("ordered_at", sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "service_material",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenant.id"), nullable=False, index=True),
        sa.Column("service_id", sa.Integer(), sa.ForeignKey("service.id"), nullable=False),
        sa.Column("material_id", sa.Integer(), sa.ForeignKey("material.id"), nullable=False),
        sa.Column("quantity_required", sa.Numeric(precision=10, scale=2), nullable=False),
    )

def downgrade() -> None:
    op.drop_table("service_material")
    op.drop_table("purchase_order")
    op.drop_table("stock_entry")
    op.drop_table("material")
    op.drop_table("salon_closed_day")
    op.drop_table("salon_working_hours")
