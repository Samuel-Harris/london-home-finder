from __future__ import annotations

from lhf.db.base import Base
from sqlalchemy import JSON, Float, Integer, String, Text, UniqueConstraint
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
    property_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Rightmove propertyType as stored",
    )
    property_sub_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Rightmove propertySubType as stored",
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
    key_features: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Rightmove keyFeatures joined with newlines",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Rightmove text.description as stored",
    )
    bathrooms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Bathroom count",
    )
    garden: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Rightmove features.garden displayText joined with newlines",
    )
    parking: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Rightmove features.parking displayText joined with newlines",
    )
    latitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="Rightmove location.latitude",
    )
    longitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="Rightmove location.longitude",
    )
    nearest_stations: Mapped[list[dict[str, object]] | None] = mapped_column(
        JSON,
        nullable=True,
        comment="Rightmove nearestStations as stored",
    )
    listing_update_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Rightmove listingHistory.listingUpdateReason or search addedOrReduced",
    )
    listing_update_date: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Rightmove listingUpdate.listingUpdateDate as stored",
    )
    first_visible_date: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Rightmove firstVisibleDate as stored",
    )
