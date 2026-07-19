"""Add users and admin_users tables, extend scheduler_jobs with job_aps_id
and paused, and backfill job_aps_id for existing scheduler_jobs rows.

Three schema changes rolled into one migration to keep the upgrade atomic:

  1. users        — end-user email/password accounts (Google users get
    firebase_uid, password_hash NULL).
  2. admin_users  — admin accounts with separate JWT issuance. Two
    superadmins are seeded at runtime (not in the migration) via
    core.admin_auth.seed_admins_if_empty so password hashes use bcrypt
    (a Python-side concern).
  3. scheduler_jobs — add job_aps_id (stable APScheduler job id) and
    paused (boolean). Backfill existing rows: job_type='refresh' ->
    'refresh', job_type='analytics' -> 'analytics'. crawl_source rows
    (per-source) stay NULL (manually triggered, not scheduled).

Revision ID: 0008_auth_jobs
Revises: 0007_nyetapiole
Create Date: 2026-07-18
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0008_auth_jobs"
down_revision = "0007_nyetapiole"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- users ---
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("email", sa.String(256), nullable=True),
        sa.Column("password_hash", sa.String(255), nullable=True),
        sa.Column("display_name", sa.String(120), nullable=True),
        sa.Column("phone", sa.String(40), nullable=True),
        sa.Column("firebase_uid", sa.String(128), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False,
                  server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("email", name="uq_users_email"),
        sa.UniqueConstraint("firebase_uid", name="uq_users_firebase_uid"),
    )
    op.create_index("idx_users_email", "users", ["email"])

    # --- admin_users ---
    op.create_table(
        "admin_users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("username", sa.String(80), nullable=True),
        sa.Column("email", sa.String(256), nullable=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False,
                  server_default=sa.true()),
        sa.Column("is_superadmin", sa.Boolean(), nullable=False,
                  server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("username", name="uq_admin_users_username"),
        sa.UniqueConstraint("email", name="uq_admin_users_email"),
    )
    op.create_index("idx_admin_users_username", "admin_users", ["username"])
    op.create_index("idx_admin_users_email", "admin_users", ["email"])

    # --- scheduler_jobs extension ---
    op.add_column(
        "scheduler_jobs",
        sa.Column("job_aps_id", sa.String(60), nullable=True),
    )
    op.add_column(
        "scheduler_jobs",
        sa.Column("paused", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index("idx_scheduler_jobs_aps_id", "scheduler_jobs", ["job_aps_id"])

    # Backfill job_aps_id for existing rows. crawl_all may not have a row yet
    # (created lazily by _get_or_create_job on first run); refresh and
    # analytics rows always exist after the first scheduled run. crawl_source
    # rows (per-source) keep NULL — they are manually triggered.
    bind = op.get_bind()
    bind.execute(sa.text(
        "UPDATE scheduler_jobs SET job_aps_id = 'refresh' "
        "WHERE job_type = 'refresh' AND job_aps_id IS NULL"
    ))
    bind.execute(sa.text(
        "UPDATE scheduler_jobs SET job_aps_id = 'analytics' "
        "WHERE job_type = 'analytics' AND job_aps_id IS NULL"
    ))


def downgrade() -> None:
    op.drop_index("idx_scheduler_jobs_aps_id", table_name="scheduler_jobs")
    op.drop_column("scheduler_jobs", "paused")
    op.drop_column("scheduler_jobs", "job_aps_id")

    op.drop_index("idx_admin_users_email", table_name="admin_users")
    op.drop_index("idx_admin_users_username", table_name="admin_users")
    op.drop_table("admin_users")

    op.drop_index("idx_users_email", table_name="users")
    op.drop_table("users")