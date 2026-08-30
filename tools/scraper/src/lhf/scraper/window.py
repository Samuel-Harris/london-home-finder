from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True, kw_only=True)
class IngestWindow:
    min_price: int = 350_000
    max_price: int = 800_000
    min_bedrooms: int | None = 2
    property_types: tuple[str, ...] | None = (
        "detached",
        "semi-detached",
        "terraced",
        "bungalow",
    )
    tenure: str | None = "FREEHOLD"

    def __post_init__(self) -> None:
        if self.min_price <= 0:
            raise ValueError("min_price must be positive")
        if self.max_price < self.min_price:
            raise ValueError("max_price must not be less than min_price")
        if self.min_bedrooms is not None and self.min_bedrooms < 0:
            raise ValueError("min_bedrooms must not be negative")


DEFAULT_WINDOW = IngestWindow()
