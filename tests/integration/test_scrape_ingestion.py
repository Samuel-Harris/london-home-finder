from pathlib import Path

from lhf.db.session import create_session_factory
from lhf.db_app.migrations import upgrade_database
from lhf.listings.listing import ListingDraft
from lhf.listings.listing_repository import ListingRepository
from lhf.scraper.rightmove.detail import parse_property_data
from lhf.scraper.rightmove.map_listing import map_listing
from lhf.scraper.rightmove.search import parse_search_page
from sqlalchemy import text

FIXTURES = (
    Path(__file__).resolve().parents[2] / "tools" / "scraper" / "tests" / "rightmove" / "fixtures"
)


def test_recorded_rightmove_html_round_trips_through_migrated_sqlite(tmp_path: Path) -> None:
    database_path = tmp_path / "integration.sqlite3"
    upgrade_database(database_path)
    repository = ListingRepository(create_session_factory(database_path))

    first = _drafts_from_recorded_html()
    assert repository.replace_all(first) == 2
    listings = repository.list_all()
    assert [(listing.external_id, listing.postcode) for listing in listings] == [
        ("111111", None),
        ("222222", "SW1A 2AA"),
    ]
    assert listings[0].asking_price_gbp is None
    assert listings[0].property_type == "flat"
    assert listings[0].property_sub_type == "Maisonette"
    assert listings[0].annual_service_charge_gbp == 2400
    assert listings[0].key_features == "Private garden\nLift"
    assert listings[0].description == "A leasehold maisonette.<br /><br />Private garden."
    assert listings[0].bathrooms == 1
    assert listings[0].garden == "Yes"
    assert listings[0].nearest_stations is not None
    assert len(listings[0].nearest_stations) == 2
    assert listings[1].years_remaining_on_lease is None
    assert listings[1].garden == "Private garden"
    assert listings[1].nearest_stations is not None
    assert len(listings[1].nearest_stations) == 3
    assert listings[1].property_type == "house"
    assert listings[1].property_sub_type == "Terraced"
    assert listings[1].key_features == "Rear garden\nPeriod features"

    replacement = [
        ListingDraft(
            source="rightmove",
            external_id="333333",
            url="https://www.rightmove.co.uk/properties/333333",
            display_address="A later snapshot",
        )
    ]
    assert repository.replace_all(replacement) == 1
    assert [listing.external_id for listing in repository.list_all()] == ["333333"]

    sessions = create_session_factory(database_path)
    with sessions() as session:
        assert session.scalar(text("PRAGMA foreign_keys")) == 1
        assert session.scalar(text("PRAGMA journal_mode")) == "wal"
        assert session.scalar(text("PRAGMA busy_timeout")) == 5000


def _drafts_from_recorded_html() -> list[ListingDraft]:
    cards = parse_search_page((FIXTURES / "search.html").read_text(encoding="utf-8")).properties
    details = {
        "111111": parse_property_data(
            (FIXTURES / "detail_leasehold.html").read_text(encoding="utf-8")
        ),
        "222222": parse_property_data(
            (FIXTURES / "detail_freehold.html").read_text(encoding="utf-8")
        ),
    }
    drafts: list[ListingDraft] = []
    seen: set[str] = set()
    for card in cards:
        if card.listing_id in seen:
            continue
        seen.add(card.listing_id)
        drafts.append(map_listing(card, details[card.listing_id]))
    return drafts
