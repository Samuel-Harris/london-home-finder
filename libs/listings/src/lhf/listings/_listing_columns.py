from __future__ import annotations

from sqlalchemy import JSON, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column


class ListingColumns:
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source: Mapped[str] = mapped_column(String(100))
    external_id: Mapped[str] = mapped_column(String(200))
    url: Mapped[str] = mapped_column(String(2048))
    display_address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    asking_price_gbp: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Numeric asking price in GBP; NULL for POA",
    )
    price_qualifier: Mapped[str | None] = mapped_column(String(100), nullable=True)
    bedrooms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    property_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    property_sub_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    postcode: Mapped[str | None] = mapped_column(String(8), nullable=True, index=True)
    floor_area_sqm: Mapped[float | None] = mapped_column(Float, nullable=True)
    tenure_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    years_remaining_on_lease: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Remaining lease years; NULL when not a positive leasehold figure",
    )
    annual_service_charge_gbp: Mapped[int | None] = mapped_column(Integer, nullable=True)
    annual_ground_rent_gbp: Mapped[int | None] = mapped_column(Integer, nullable=True)
    key_features: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    bathrooms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    garden: Mapped[str | None] = mapped_column(Text, nullable=True)
    parking: Mapped[str | None] = mapped_column(Text, nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    nearest_stations: Mapped[list[dict[str, object]] | None] = mapped_column(JSON, nullable=True)
    listing_update_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    listing_update_date: Mapped[str | None] = mapped_column(Text, nullable=True)
    first_visible_date: Mapped[str | None] = mapped_column(Text, nullable=True)
