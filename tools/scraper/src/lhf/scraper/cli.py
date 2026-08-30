from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from lhf.scraper.scrape import scrape
from lhf.scraper.window import DEFAULT_WINDOW, IngestWindow


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Scrape Rightmove London BUY listings into SQLite."
    )
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--min-price", type=int, default=DEFAULT_WINDOW.min_price)
    parser.add_argument("--max-price", type=int, default=DEFAULT_WINDOW.max_price)
    parser.add_argument("--min-bedrooms", type=int, default=DEFAULT_WINDOW.min_bedrooms or 0)
    parser.add_argument(
        "--property-types",
        default=",".join(DEFAULT_WINDOW.property_types or ()),
        help="Comma-separated property types, or 'any' to omit.",
    )
    parser.add_argument(
        "--tenure",
        default=DEFAULT_WINDOW.tenure or "any",
        help="Tenure type, or 'any' to omit.",
    )
    parser.add_argument("--max-pages", type=int, default=None)
    parser.add_argument("--resume", action="store_true")
    arguments = parser.parse_args(argv)
    try:
        count = scrape(
            arguments.database,
            window=IngestWindow(
                min_price=arguments.min_price,
                max_price=arguments.max_price,
                min_bedrooms=_min_bedrooms(arguments.min_bedrooms),
                property_types=_property_types(arguments.property_types),
                tenure=_tenure(arguments.tenure),
            ),
            max_pages=arguments.max_pages,
            resume=arguments.resume,
        )
    except ValueError as exc:
        parser.error(str(exc))
    print(f"Replaced listings with {count} rows in {arguments.database}.")
    return 0


def _min_bedrooms(value: int) -> int | None:
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
