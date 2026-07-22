from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import URL

DB_APP_ROOT = Path(__file__).resolve().parents[2]


def upgrade_database(database_path: str | Path) -> None:
    path = Path(database_path).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    configuration = Config(DB_APP_ROOT / "alembic.ini")
    database_url = URL.create("sqlite+pysqlite", database=path.as_posix())
    configuration.set_main_option(
        "sqlalchemy.url", database_url.render_as_string(hide_password=False)
    )
    command.upgrade(configuration, "head")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Upgrade a London Home Finder database.")
    parser.add_argument("database", type=Path)
    arguments = parser.parse_args(argv)
    upgrade_database(arguments.database)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
