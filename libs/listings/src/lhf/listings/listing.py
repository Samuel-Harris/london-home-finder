from __future__ import annotations

import re
from dataclasses import dataclass

_POSTCODE_PATTERN = re.compile(r"^[A-Z]{1,2}\d[A-Z\d]?\d[A-Z]{2}$")


@dataclass(frozen=True, slots=True)
class ListingDraft:
    source: str
    external_id: str
    title: str
    asking_price_gbp: int
    postcode: str
    url: str
    floor_area_sqm: float | None = None

    def __post_init__(self) -> None:
        for field_name in ("source", "external_id", "title", "url"):
            if not getattr(self, field_name).strip():
                raise ValueError(f"{field_name} must not be blank")
        if self.asking_price_gbp <= 0:
            raise ValueError("asking_price_gbp must be positive")
        if self.floor_area_sqm is not None and self.floor_area_sqm <= 0:
            raise ValueError("floor_area_sqm must be positive when provided")
        object.__setattr__(self, "postcode", normalise_postcode(self.postcode))


@dataclass(frozen=True, slots=True)
class Listing:
    id: int
    source: str
    external_id: str
    title: str
    asking_price_gbp: int
    postcode: str
    url: str
    floor_area_sqm: float | None


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
