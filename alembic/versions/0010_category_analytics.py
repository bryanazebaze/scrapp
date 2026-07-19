"""Add category + per-sqm price columns to neighborhood_analytics.

Supports the category-aware analytics refactor:
- `category` ('Structure' | 'Land' | NULL) tags each analytics row so callers
  can distinguish building vs land comparisons.
- `min_price_per_sqm`, `max_price_per_sqm`, `avg_price_per_sqm` store
  price-per-m2 stats for Land rows (where total price is meaningless without
  area). Structure rows leave these NULL and keep using total-price columns.

The existing `price_per_sqm` column is retained for backwards compatibility
(legacy single-mean value); the new columns are the canonical source going
forward. Existing rows are repopulated by `python cli.py analytics` after
the migration applies.

Revision ID: 0010_category_analytics
Revises: 0009_chambre_bedrooms_plus_one
"""
from alembic import op
import sqlalchemy as sa


revision = "0010_category_analytics"
down_revision = "0009_chambre_bedrooms_plus_one"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("neighborhood_analytics",
                  sa.Column("category", sa.String(length=12), nullable=True))
    op.add_column("neighborhood_analytics",
                  sa.Column("min_price_per_sqm", sa.Float(), nullable=True))
    op.add_column("neighborhood_analytics",
                  sa.Column("max_price_per_sqm", sa.Float(), nullable=True))
    op.add_column("neighborhood_analytics",
                  sa.Column("avg_price_per_sqm", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("neighborhood_analytics", "avg_price_per_sqm")
    op.drop_column("neighborhood_analytics", "max_price_per_sqm")
    op.drop_column("neighborhood_analytics", "min_price_per_sqm")
    op.drop_column("neighborhood_analytics", "category")