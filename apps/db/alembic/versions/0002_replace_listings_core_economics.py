"""Replace listings with named core-economics columns."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_replace_listings_core_economics"
down_revision: str | None = "0001_create_listings"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_index("ix_listings_postcode", table_name="listings")
    op.drop_table("listings")
    op.create_table(
        "listings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=100), nullable=False),
        sa.Column("external_id", sa.String(length=200), nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=False),
        sa.Column(
            "display_address",
            sa.String(length=500),
            nullable=True,
            comment="Rightmove display address",
        ),
        sa.Column(
            "asking_price_gbp",
            sa.Integer(),
            nullable=True,
            comment="Numeric asking price in GBP; NULL for POA",
        ),
        sa.Column(
            "price_qualifier",
            sa.String(length=100),
            nullable=True,
            comment="Qualifier that changes the price's meaning (Guide Price, OIEO, From, …)",
        ),
        sa.Column(
            "bedrooms",
            sa.Integer(),
            nullable=True,
            comment="Bedroom count",
        ),
        sa.Column(
            "postcode",
            sa.String(length=8),
            nullable=True,
            comment="Normalised UK postcode from detail address.outcode + address.incode",
        ),
        sa.Column(
            "floor_area_sqm",
            sa.Float(),
            nullable=True,
            comment="Size in square metres",
        ),
        sa.Column(
            "tenure_type",
            sa.String(length=50),
            nullable=True,
            comment="Rightmove tenure.tenureType as stored",
        ),
        sa.Column(
            "years_remaining_on_lease",
            sa.Integer(),
            nullable=True,
            comment="Remaining lease years; NULL when not a positive leasehold figure",
        ),
        sa.Column(
            "annual_service_charge_gbp",
            sa.Integer(),
            nullable=True,
            comment="Annual service charge",
        ),
        sa.Column(
            "annual_ground_rent_gbp",
            sa.Integer(),
            nullable=True,
            comment="Annual ground rent",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source", "external_id"),
    )
    op.create_index("ix_listings_postcode", "listings", ["postcode"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_listings_postcode", table_name="listings")
    op.drop_table("listings")
    op.create_table(
        "listings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=100), nullable=False),
        sa.Column("external_id", sa.String(length=200), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("asking_price_gbp", sa.Integer(), nullable=False),
        sa.Column("postcode", sa.String(length=8), nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=False),
        sa.Column("floor_area_sqm", sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source", "external_id"),
    )
    op.create_index("ix_listings_postcode", "listings", ["postcode"], unique=False)
