from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from lhf_scraper.fixture import import_fixture


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Manually ingest London home data.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    fixture_parser = subparsers.add_parser(
        "import-fixture", description="Import a recorded JSON fixture."
    )
    fixture_parser.add_argument("fixture", type=Path)
    fixture_parser.add_argument("--database", type=Path, required=True)
    arguments = parser.parse_args(argv)

    if arguments.command == "import-fixture":
        imported_count = import_fixture(arguments.fixture, arguments.database)
        print(f"Imported {imported_count} listings into {arguments.database}.")
        return 0

    parser.error(f"unsupported command: {arguments.command}")
