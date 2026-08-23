from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from lhf.scraper.scrape import DEFAULT_MAX_PRICE, DEFAULT_MIN_PRICE, scrape


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Scrape Rightmove London BUY listings into SQLite."
    )
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--min-price", type=int, default=DEFAULT_MIN_PRICE)
    parser.add_argument("--max-price", type=int, default=DEFAULT_MAX_PRICE)
    parser.add_argument("--max-pages", type=int, default=None)
    parser.add_argument("--resume", action="store_true")
    arguments = parser.parse_args(argv)
    try:
        count = scrape(
            arguments.database,
            min_price=arguments.min_price,
            max_price=arguments.max_price,
            max_pages=arguments.max_pages,
            resume=arguments.resume,
        )
    except ValueError as exc:
        parser.error(str(exc))
    print(f"Replaced listings with {count} rows in {arguments.database}.")
    return 0
