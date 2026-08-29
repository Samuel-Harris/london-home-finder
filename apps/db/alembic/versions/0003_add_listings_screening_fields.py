"""Add listing screening columns."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_add_listings_screening_fields"
down_revision: str | None = "0002_replace_listings_core_economics"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "listings",
        sa.Column(
            "property_type",
            sa.String(length=50),
            nullable=True,
            comment="Rightmove propertyType as stored",
        ),
    )
    op.add_column(
        "listings",
        sa.Column(
            "property_sub_type",
            sa.String(length=100),
            nullable=True,
            comment="Rightmove propertySubType as stored",
        ),
    )
    op.add_column(
        "listings",
        sa.Column(
            "key_features",
            sa.Text(),
            nullable=True,
            comment="Rightmove keyFeatures joined with newlines",
        ),
    )
    op.add_column(
        "listings",
        sa.Column(
            "description",
            sa.Text(),
            nullable=True,
            comment="Rightmove text.description as stored",
        ),
    )
    op.add_column(
        "listings",
        sa.Column("bathrooms", sa.Integer(), nullable=True, comment="Bathroom count"),
    )
    op.add_column(
        "listings",
        sa.Column(
            "garden",
            sa.Text(),
            nullable=True,
            comment="Rightmove features.garden displayText joined with newlines",
        ),
    )
    op.add_column(
        "listings",
        sa.Column(
            "parking",
            sa.Text(),
            nullable=True,
            comment="Rightmove features.parking displayText joined with newlines",
        ),
    )
    op.add_column(
        "listings",
        sa.Column("latitude", sa.Float(), nullable=True, comment="Rightmove location.latitude"),
    )
    op.add_column(
        "listings",
        sa.Column("longitude", sa.Float(), nullable=True, comment="Rightmove location.longitude"),
    )
    op.add_column(
        "listings",
        sa.Column(
            "nearest_stations",
            sa.JSON(),
            nullable=True,
            comment="Rightmove nearestStations as stored",
        ),
    )
    op.add_column(
        "listings",
        sa.Column(
            "listing_update_reason",
            sa.Text(),
            nullable=True,
            comment="Rightmove listingHistory.listingUpdateReason or search addedOrReduced",
        ),
    )
    op.add_column(
        "listings",
        sa.Column(
            "listing_update_date",
            sa.Text(),
            nullable=True,
            comment="Rightmove listingUpdate.listingUpdateDate as stored",
        ),
    )
    op.add_column(
        "listings",
        sa.Column(
            "first_visible_date",
            sa.Text(),
            nullable=True,
            comment="Rightmove firstVisibleDate as stored",
        ),
    )


def downgrade() -> None:
    op.drop_column("listings", "first_visible_date")
    op.drop_column("listings", "listing_update_date")
    op.drop_column("listings", "listing_update_reason")
    op.drop_column("listings", "nearest_stations")
    op.drop_column("listings", "longitude")
    op.drop_column("listings", "latitude")
    op.drop_column("listings", "parking")
    op.drop_column("listings", "garden")
    op.drop_column("listings", "bathrooms")
    op.drop_column("listings", "description")
    op.drop_column("listings", "key_features")
    op.drop_column("listings", "property_sub_type")
    op.drop_column("listings", "property_type")
