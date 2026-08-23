from __future__ import annotations

import re
from dataclasses import dataclass

_POSTCODE_PATTERN = re.compile(r"^[A-Z]{1,2}\d[A-Z\d]?\d[A-Z]{2}$")


@dataclass(frozen=True, slots=True)
class NearestStation:
    name: str
    types: tuple[str, ...]
    distance: float | None = None
    unit: str | None = None


@dataclass(frozen=True, slots=True)
class ListingDraft:
    source: str
    external_id: str
    url: str
    display_address: str | None = None
    asking_price_gbp: int | None = None
    price_qualifier: str | None = None
    bedrooms: int | None = None
    property_type: str | None = None
    property_sub_type: str | None = None
    postcode: str | None = None
    floor_area_sqm: float | None = None
    tenure_type: str | None = None
    years_remaining_on_lease: int | None = None
    annual_service_charge_gbp: int | None = None
    annual_ground_rent_gbp: int | None = None
    key_features: str | None = None
    description: str | None = None
    bathrooms: int | None = None
    garden: str | None = None
    parking: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    nearest_stations: tuple[NearestStation, ...] | None = None
    listing_update_reason: str | None = None
    listing_update_date: str | None = None
    first_visible_date: str | None = None

    def __post_init__(self) -> None:
        for field_name in ("source", "external_id", "url"):
            if not getattr(self, field_name).strip():
                raise ValueError(f"{field_name} must not be blank")
        if self.asking_price_gbp is not None and self.asking_price_gbp <= 0:
            raise ValueError("asking_price_gbp must be positive")
        if self.floor_area_sqm is not None and self.floor_area_sqm <= 0:
            raise ValueError("floor_area_sqm must be positive when provided")
        if self.years_remaining_on_lease is not None and self.years_remaining_on_lease <= 0:
            raise ValueError("years_remaining_on_lease must be positive when provided")
        if self.postcode is None or not self.postcode.strip():
            object.__setattr__(self, "postcode", None)
        else:
            object.__setattr__(self, "postcode", normalise_postcode(self.postcode))
        if not self.nearest_stations:
            object.__setattr__(self, "nearest_stations", None)


@dataclass(frozen=True, slots=True)
class Listing:
    id: int
    source: str
    external_id: str
    url: str
    display_address: str | None
    asking_price_gbp: int | None
    price_qualifier: str | None
    bedrooms: int | None
    property_type: str | None
    property_sub_type: str | None
    postcode: str | None
    floor_area_sqm: float | None
    tenure_type: str | None
    years_remaining_on_lease: int | None
    annual_service_charge_gbp: int | None
    annual_ground_rent_gbp: int | None
    key_features: str | None
    description: str | None
    bathrooms: int | None
    garden: str | None
    parking: str | None
    latitude: float | None
    longitude: float | None
    nearest_stations: tuple[NearestStation, ...] | None
    listing_update_reason: str | None
    listing_update_date: str | None
    first_visible_date: str | None


def normalise_postcode(postcode: str) -> str:
    """Return a compact UK postcode in its canonical single-space form."""
    compact = "".join(postcode.upper().split())
    if not _POSTCODE_PATTERN.fullmatch(compact):
        raise ValueError(f"invalid UK postcode: {postcode!r}")
    return f"{compact[:-3]} {compact[-3:]}"


def is_within_budget(asking_price_gbp: int, maximum_price_gbp: int) -> bool:
    """Return whether a positive asking price is within a non-negative budget."""
    if asking_price_gbp <= 0:
        raise ValueError("asking_price_gbp must be positive")
    if maximum_price_gbp < 0:
        raise ValueError("maximum_price_gbp must not be negative")
    return asking_price_gbp <= maximum_price_gbp


def price_per_square_metre(asking_price_gbp: int, floor_area_sqm: float) -> float:
    """Calculate a listing's asking price per square metre."""
    if asking_price_gbp <= 0:
        raise ValueError("asking_price_gbp must be positive")
    if floor_area_sqm <= 0:
        raise ValueError("floor_area_sqm must be positive")
    return asking_price_gbp / floor_area_sqm
