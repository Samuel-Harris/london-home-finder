"""Create the listings table."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_create_listings"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
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


def downgrade() -> None:
    op.drop_index("ix_listings_postcode", table_name="listings")
    op.drop_table("listings")
