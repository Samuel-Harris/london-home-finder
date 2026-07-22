from __future__ import annotations

from lhf.db.base import Base
from sqlalchemy import Float, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column


class ListingRow(Base):
    __tablename__ = "listings"
    __table_args__ = (UniqueConstraint("source", "external_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source: Mapped[str] = mapped_column(String(100))
    external_id: Mapped[str] = mapped_column(String(200))
    title: Mapped[str] = mapped_column(String(500))
    asking_price_gbp: Mapped[int] = mapped_column(Integer)
    postcode: Mapped[str] = mapped_column(String(8), index=True)
    url: Mapped[str] = mapped_column(String(2048))
    floor_area_sqm: Mapped[float | None] = mapped_column(Float, nullable=True)
