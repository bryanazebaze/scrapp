"""Add payment_records table for Notch Pay transaction audit trail.

Each row records a terminal Notch Pay transaction (complete | failed |
canceled | expired) for a Firebase user.  The ``reference`` column is
unique (it is the Notch Pay payment reference we generate).

Revision ID: 0006_payments
Revises: 0005_bilingual
Create Date: 2026-07-01
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB


revision = "0006_payments"
down_revision = "0005_bilingual"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "payment_records",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("firebase_uid", sa.String(128), nullable=False),
        sa.Column("email", sa.String(256), nullable=True),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("reference", sa.String(128), nullable=False, unique=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("notchpay_response", JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_payment_records_uid", "payment_records", ["firebase_uid"])
    op.create_index(
        "idx_payment_records_reference",
        "payment_records",
        ["reference"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("idx_payment_records_reference", table_name="payment_records")
    op.drop_index("idx_payment_records_uid", table_name="payment_records")
    op.drop_table("payment_records")