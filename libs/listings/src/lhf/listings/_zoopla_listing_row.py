from __future__ import annotations

from lhf.db.base import Base
from lhf.listings._listing_columns import ListingColumns
from sqlalchemy import UniqueConstraint


class ZooplaListingRow(ListingColumns, Base):
    __tablename__ = "listings_zoopla"
    __table_args__ = (UniqueConstraint("source", "external_id"),)
