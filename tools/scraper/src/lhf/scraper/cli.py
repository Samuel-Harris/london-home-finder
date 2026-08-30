from __future__ import annotations

import argparse
from collections.abc import Callable, Sequence
from pathlib import Path

from lhf.scraper.onthemarket.checkpoint import checkpoint_path as onthemarket_checkpoint_path
from lhf.scraper.onthemarket.scrape import scrape as scrape_onthemarket
from lhf.scraper.rightmove.checkpoint import checkpoint_path as rightmove_checkpoint_path
from lhf.scraper.rightmove.scrape import scrape as scrape_rightmove
from lhf.scraper.window import DEFAULT_WINDOW, IngestWindow


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Scrape Rightmove and OnTheMarket London BUY listings into SQLite."
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
        window = IngestWindow(
            min_price=arguments.min_price,
            max_price=arguments.max_price,
            min_bedrooms=_min_bedrooms(arguments.min_bedrooms),
            property_types=_property_types(arguments.property_types),
            tenure=_tenure(arguments.tenure),
        )
        for name, scrape, resume_source in _source_runs(arguments.database, arguments.resume):
            count = scrape(
                arguments.database,
                window=window,
                max_pages=arguments.max_pages,
                resume=resume_source,
            )
            print(f"Replaced {name} listings with {count} rows in {arguments.database}.")
    except ValueError as exc:
        parser.error(str(exc))
    return 0


def _source_runs(database: Path, resume: bool) -> list[tuple[str, Callable[..., int], bool]]:
    sources: tuple[tuple[str, Callable[..., int], Callable[[Path], Path]], ...] = (
        ("rightmove", scrape_rightmove, rightmove_checkpoint_path),
        ("onthemarket", scrape_onthemarket, onthemarket_checkpoint_path),
    )
    if not resume:
        return [(name, scrape, False) for name, scrape, _checkpoint in sources]
    present = tuple(
        checkpoint_for(database).is_file() for _name, _scrape, checkpoint_for in sources
    )
    if not any(present):
        raise ValueError(f"no scrape checkpoint to resume at {database}")
    runs: list[tuple[str, Callable[..., int], bool]] = []
    earlier_in_progress = False
    for (name, scrape, _checkpoint), has_checkpoint in zip(sources, present, strict=True):
        if has_checkpoint:
            runs.append((name, scrape, True))
            earlier_in_progress = True
        elif earlier_in_progress:
            runs.append((name, scrape, False))
    return runs


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
