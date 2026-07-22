from pathlib import Path

from lhf.db.session import create_session_factory
from lhf.db_app.migrations import upgrade_database
from lhf.listings.listing_repository import ListingRepository
from lhf.scraper.fixture import import_fixture
from sqlalchemy import text

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "london_listings.json"


def test_recorded_fixture_round_trips_through_migrated_sqlite(tmp_path: Path) -> None:
    database_path = tmp_path / "integration.sqlite3"
    upgrade_database(database_path)

    assert import_fixture(FIXTURE_PATH, database_path) == 2
    assert import_fixture(FIXTURE_PATH, database_path) == 2

    sessions = create_session_factory(database_path)
    listings = ListingRepository(sessions).list_all()
    assert [(listing.external_id, listing.postcode) for listing in listings] == [
        ("westminster-001", "SW1H 9LL"),
        ("hackney-002", "E8 1EA"),
    ]

    with sessions() as session:
        assert session.scalar(text("PRAGMA foreign_keys")) == 1
        assert session.scalar(text("PRAGMA journal_mode")) == "wal"
        assert session.scalar(text("PRAGMA busy_timeout")) == 5000
