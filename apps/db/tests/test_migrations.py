from pathlib import Path

from lhf.db_app.migrations import upgrade_database
from sqlalchemy import create_engine, inspect


def test_upgrade_database_creates_listings_table(tmp_path: Path) -> None:
    database_path = tmp_path / "migrated.sqlite3"
    upgrade_database(database_path)

    inspector = inspect(create_engine(f"sqlite+pysqlite:///{database_path.as_posix()}"))
    assert inspector.has_table("listings")
    assert {column["name"] for column in inspector.get_columns("listings")} == {
        "id",
        "source",
        "external_id",
        "title",
        "asking_price_gbp",
        "postcode",
        "url",
        "floor_area_sqm",
    }
