from pathlib import Path

from lhf.db.base import metadata
from lhf.db.session import create_session_factory
from lhf.listings.listing import ListingDraft
from lhf.listings.listing_repository import ListingRepository


def test_repository_replace_all_replaces_the_whole_table(tmp_path: Path) -> None:
    repository = _repository(tmp_path)
    repository.replace_all(
        [
            ListingDraft(
                source="example",
                external_id="home-1",
                display_address="Original address",
                asking_price_gbp=650_000,
                postcode="SW1A 1AA",
                url="https://example.test/home-1",
            )
        ]
    )
    repository.replace_all(
        [
            ListingDraft(
                source="example",
                external_id="home-2",
                display_address="Replacement address",
                asking_price_gbp=500_000,
                postcode="E8 1EA",
                url="https://example.test/home-2",
            )
        ]
    )

    listings = repository.list_all()
    assert [(listing.external_id, listing.display_address) for listing in listings] == [
        ("home-2", "Replacement address")
    ]


def test_repository_empty_replace_all_wipes_the_table(tmp_path: Path) -> None:
    repository = _repository(tmp_path)
    repository.replace_all(
        [
            ListingDraft(
                source="example",
                external_id="home-1",
                url="https://example.test/home-1",
            )
        ]
    )

    assert repository.replace_all([]) == 0
    assert repository.list_all() == []


def _repository(tmp_path: Path) -> ListingRepository:
    sessions = create_session_factory(tmp_path / "repository.sqlite3")
    metadata.create_all(sessions.kw["bind"])
    return ListingRepository(sessions)
