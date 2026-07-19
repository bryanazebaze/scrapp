"""Add listing_purpose column to canonical_properties and backfill from title.

Distinguishes rental listings ('rent') from sale listings ('sale') so that
sale-price analytics stop pooling monthly rents with sale prices. Also
reclassifies 4 misclassified properties whose title says 'Terrain' but
whose property_type was Maison/Appartement.
"""
from alembic import op
import sqlalchemy as sa


revision = "0011_listing_purpose"
down_revision = "0010_category_analytics"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "canonical_properties",
        sa.Column("listing_purpose", sa.String(10), nullable=True),
    )
    op.create_index(
        "ix_canonical_listing_purpose",
        "canonical_properties",
        ["listing_purpose"],
    )

    # Backfill listing_purpose from the title.
    op.execute(
        """
        UPDATE canonical_properties
        SET listing_purpose = 'rent'
        WHERE listing_purpose IS NULL
          AND (title_canonical ILIKE '%à louer%'
               OR title_canonical ILIKE '%for rent%'
               OR title_canonical ILIKE '%meublé%')
        """
    )
    op.execute(
        """
        UPDATE canonical_properties
        SET listing_purpose = 'sale'
        WHERE listing_purpose IS NULL
          AND (title_canonical ILIKE '%à vendre%'
               OR title_canonical ILIKE '%for sale%'
               OR title_canonical ILIKE '%terrain%'
               OR title_canonical ILIKE '% land%'
               OR title_canonical ILIKE '%lot%')
        """
    )

    # Reclassify misclassified properties: title says Terrain/Land but
    # property_type was Maison or Appartement.
    op.execute(
        """
        UPDATE canonical_properties
        SET property_type = 'Terrain'
        WHERE property_type IN ('Maison', 'Appartement')
          AND (title_canonical ILIKE '%terrain%' OR title_canonical ILIKE '%land%')
        """
    )


def downgrade() -> None:
    op.drop_index("ix_canonical_listing_purpose", table_name="canonical_properties")
    op.drop_column("canonical_properties", "listing_purpose")