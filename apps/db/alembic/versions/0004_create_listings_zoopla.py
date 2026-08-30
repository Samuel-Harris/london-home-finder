"""Create listings_zoopla for Zoopla ingest."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_create_listings_zoopla"
down_revision: str | None = "0003_add_listings_screening_fields"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "listings_zoopla",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=100), nullable=False),
        sa.Column("external_id", sa.String(length=200), nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=False),
        sa.Column("display_address", sa.String(length=500), nullable=True),
        sa.Column(
            "asking_price_gbp",
            sa.Integer(),
            nullable=True,
            comment="Numeric asking price in GBP; NULL for POA",
        ),
        sa.Column("price_qualifier", sa.String(length=100), nullable=True),
        sa.Column("bedrooms", sa.Integer(), nullable=True),
        sa.Column("property_type", sa.String(length=50), nullable=True),
        sa.Column("property_sub_type", sa.String(length=100), nullable=True),
        sa.Column("postcode", sa.String(length=8), nullable=True),
        sa.Column("floor_area_sqm", sa.Float(), nullable=True),
        sa.Column("tenure_type", sa.String(length=50), nullable=True),
        sa.Column(
            "years_remaining_on_lease",
            sa.Integer(),
            nullable=True,
            comment="Remaining lease years; NULL when not a positive leasehold figure",
        ),
        sa.Column("annual_service_charge_gbp", sa.Integer(), nullable=True),
        sa.Column("annual_ground_rent_gbp", sa.Integer(), nullable=True),
        sa.Column("key_features", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("bathrooms", sa.Integer(), nullable=True),
        sa.Column("garden", sa.Text(), nullable=True),
        sa.Column("parking", sa.Text(), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("nearest_stations", sa.JSON(), nullable=True),
        sa.Column("listing_update_reason", sa.Text(), nullable=True),
        sa.Column("listing_update_date", sa.Text(), nullable=True),
        sa.Column("first_visible_date", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source", "external_id"),
    )
    op.create_index("ix_listings_zoopla_postcode", "listings_zoopla", ["postcode"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_listings_zoopla_postcode", table_name="listings_zoopla")
    op.drop_table("listings_zoopla")
