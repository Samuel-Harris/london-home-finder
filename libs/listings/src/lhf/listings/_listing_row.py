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
    url: Mapped[str] = mapped_column(String(2048))
    display_address: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Rightmove display address",
    )
    asking_price_gbp: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Numeric asking price in GBP; NULL for POA",
    )
    price_qualifier: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Qualifier that changes the price's meaning (Guide Price, OIEO, From, …)",
    )
    bedrooms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Bedroom count",
    )
    postcode: Mapped[str | None] = mapped_column(
        String(8),
        nullable=True,
        index=True,
        comment="Normalised UK postcode from detail address.outcode + address.incode",
    )
    floor_area_sqm: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="Size in square metres",
    )
    tenure_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Rightmove tenure.tenureType as stored",
    )
    years_remaining_on_lease: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Remaining lease years; NULL when not a positive leasehold figure",
    )
    annual_service_charge_gbp: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Annual service charge",
    )
    annual_ground_rent_gbp: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Annual ground rent",
    )
