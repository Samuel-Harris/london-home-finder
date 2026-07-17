from pathlib import Path

from lhf_backend.api import ListingDraft, ListingRepository, create_session_factory, metadata


def test_repository_upserts_the_same_source_listing(tmp_path: Path) -> None:
    sessions = create_session_factory(tmp_path / "repository.sqlite3")
    metadata.create_all(sessions.kw["bind"])
    repository = ListingRepository(sessions)
    first = ListingDraft(
        source="example",
        external_id="home-1",
        title="Original title",
        asking_price_gbp=650_000,
        postcode="SW1A 1AA",
        url="https://example.test/home-1",
    )
    updated = ListingDraft(
        source="example",
        external_id="home-1",
        title="Updated title",
        asking_price_gbp=625_000,
        postcode="SW1A 1AA",
        url="https://example.test/home-1",
    )

    repository.upsert([first])
    repository.upsert([updated])

    assert [(listing.title, listing.asking_price_gbp) for listing in repository.list_all()] == [
        ("Updated title", 625_000)
    ]


def test_repository_accepts_an_empty_upsert_batch(tmp_path: Path) -> None:
    sessions = create_session_factory(tmp_path / "repository.sqlite3")
    metadata.create_all(sessions.kw["bind"])

    assert ListingRepository(sessions).upsert([]) == 0
