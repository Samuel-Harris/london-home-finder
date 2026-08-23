from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from lhf.scraper.scrape import (
    DEFAULT_MAX_PRICE,
    DEFAULT_MIN_BEDROOMS,
    DEFAULT_MIN_PRICE,
    DEFAULT_PROPERTY_TYPES,
    DEFAULT_TENURE,
    scrape,
)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Scrape Rightmove London BUY listings into SQLite."
    )
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--min-price", type=int, default=DEFAULT_MIN_PRICE)
    parser.add_argument("--max-price", type=int, default=DEFAULT_MAX_PRICE)
    parser.add_argument("--min-bedrooms", type=int, default=DEFAULT_MIN_BEDROOMS)
    parser.add_argument(
        "--property-types",
        default=",".join(DEFAULT_PROPERTY_TYPES),
        help="Comma-separated Rightmove property types, or 'any' to omit.",
    )
    parser.add_argument(
        "--tenure",
        default=DEFAULT_TENURE,
        help="Rightmove tenure type, or 'any' to omit.",
    )
    parser.add_argument("--max-pages", type=int, default=None)
    parser.add_argument("--resume", action="store_true")
    arguments = parser.parse_args(argv)
    try:
        count = scrape(
            arguments.database,
            min_price=arguments.min_price,
            max_price=arguments.max_price,
            max_pages=arguments.max_pages,
            min_bedrooms=_min_bedrooms(arguments.min_bedrooms),
            property_types=_property_types(arguments.property_types),
            tenure=_tenure(arguments.tenure),
            resume=arguments.resume,
        )
    except ValueError as exc:
        parser.error(str(exc))
    print(f"Replaced listings with {count} rows in {arguments.database}.")
    return 0


def _min_bedrooms(value: int) -> int | None:
    if value < 0:
        raise ValueError("min_bedrooms must not be negative")
    if value == 0:
        return None
    return value


def _property_types(raw: str) -> tuple[str, ...] | None:
    stripped = raw.strip()
    if stripped.lower() == "any":
        return None
    types = tuple(part.strip() for part in stripped.split(",") if part.strip())
    if not types:
        raise ValueError("property_types must be a comma-separated list or 'any'")
    return types


def _tenure(raw: str) -> str | None:
    stripped = raw.strip()
    if stripped.lower() == "any":
        return None
    if not stripped:
        raise ValueError("tenure must be a value or 'any'")
    return stripped.upper()
