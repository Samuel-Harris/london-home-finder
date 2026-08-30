from pathlib import Path

import pytest
from lhf.db.base import metadata
from lhf.db.session import create_session_factory
from lhf.listings.listing import ListingDraft, NearestStation
from lhf.listings.listing_repository import ListingRepository


def test_repository_replace_source_replaces_that_source(tmp_path: Path) -> None:
    repository = _repository(tmp_path)
    repository.replace_source(
        "example",
        [
            ListingDraft(
                source="example",
                external_id="home-1",
                display_address="Original address",
                asking_price_gbp=650_000,
                postcode="SW1A 1AA",
                url="https://example.test/home-1",
            )
        ],
    )
    repository.replace_source(
        "example",
        [
            ListingDraft(
                source="example",
                external_id="home-2",
                display_address="Replacement address",
                asking_price_gbp=500_000,
                postcode="E8 1EA",
                url="https://example.test/home-2",
            )
        ],
    )

    listings = repository.list_all()
    assert [(listing.external_id, listing.display_address) for listing in listings] == [
        ("home-2", "Replacement address")
    ]


def test_repository_replace_source_leaves_other_sources(tmp_path: Path) -> None:
    repository = _repository(tmp_path)
    repository.replace_source(
        "rightmove",
        [
            ListingDraft(
                source="rightmove",
                external_id="kept-rightmove",
                url="https://www.rightmove.co.uk/properties/kept",
            )
        ],
    )
    repository.replace_source(
        "onthemarket",
        [
            ListingDraft(
                source="onthemarket",
                external_id="otm-1",
                url="https://www.onthemarket.com/details/1/",
            )
        ],
    )
    repository.replace_source(
        "onthemarket",
        [
            ListingDraft(
                source="onthemarket",
                external_id="otm-2",
                url="https://www.onthemarket.com/details/2/",
            )
        ],
    )

    listings = repository.list_all()
    assert [(listing.source, listing.external_id) for listing in listings] == [
        ("rightmove", "kept-rightmove"),
        ("onthemarket", "otm-2"),
    ]


def test_repository_round_trips_screening_fields(tmp_path: Path) -> None:
    repository = _repository(tmp_path)
    stations = (
        NearestStation(
            name="Westminster Station",
            types=("LONDON_UNDERGROUND", "NATIONAL_TRAIN"),
            distance=0.15,
            unit="miles",
        ),
        NearestStation(
            name="Waterloo Station",
            types=("NATIONAL_TRAIN",),
            distance=0.8,
            unit="miles",
        ),
    )
    repository.replace_source(
        "rightmove",
        [
            ListingDraft(
                source="rightmove",
                external_id="home-1",
                url="https://www.rightmove.co.uk/properties/1",
                property_type="flat",
                property_sub_type="Maisonette",
                key_features="Private garden\nLift",
                description="A leasehold maisonette.<br /><br />Private garden.",
                bathrooms=1,
                garden="Yes",
                parking="Allocated underground",
                latitude=51.501,
                longitude=-0.1416,
                nearest_stations=stations,
                listing_update_reason="Reduced on 12/05/2026",
                listing_update_date="2026-05-12T10:00:00Z",
                first_visible_date="2026-01-15T12:00:00Z",
            )
        ],
    )

    listing = repository.list_all()[0]
    assert listing.property_type == "flat"
    assert listing.property_sub_type == "Maisonette"
    assert listing.key_features == "Private garden\nLift"
    assert listing.description == "A leasehold maisonette.<br /><br />Private garden."
    assert listing.bathrooms == 1
    assert listing.garden == "Yes"
    assert listing.parking == "Allocated underground"
    assert listing.latitude == 51.501
    assert listing.longitude == -0.1416
    assert listing.nearest_stations == stations
    assert listing.listing_update_reason == "Reduced on 12/05/2026"
    assert listing.listing_update_date == "2026-05-12T10:00:00Z"
    assert listing.first_visible_date == "2026-01-15T12:00:00Z"


def test_repository_empty_replace_source_wipes_that_source_only(tmp_path: Path) -> None:
    repository = _repository(tmp_path)
    repository.replace_source(
        "example",
        [
            ListingDraft(
                source="example",
                external_id="home-1",
                url="https://example.test/home-1",
            )
        ],
    )
    repository.replace_source(
        "rightmove",
        [
            ListingDraft(
                source="rightmove",
                external_id="kept",
                url="https://www.rightmove.co.uk/properties/kept",
            )
        ],
    )

    assert repository.replace_source("example", []) == 0
    listings = repository.list_all()
    assert [(listing.source, listing.external_id) for listing in listings] == [
        ("rightmove", "kept")
    ]


def test_repository_replace_source_rejects_blank_source(tmp_path: Path) -> None:
    repository = _repository(tmp_path)
    with pytest.raises(ValueError, match="source must not be blank"):
        repository.replace_source("  ", [])


def test_repository_replace_source_rejects_mismatched_draft_source(tmp_path: Path) -> None:
    repository = _repository(tmp_path)
    with pytest.raises(ValueError, match="does not match"):
        repository.replace_source(
            "onthemarket",
            [
                ListingDraft(
                    source="rightmove",
                    external_id="home-1",
                    url="https://www.rightmove.co.uk/properties/1",
                )
            ],
        )


def _repository(tmp_path: Path) -> ListingRepository:
    sessions = create_session_factory(tmp_path / "repository.sqlite3")
    metadata.create_all(sessions.kw["bind"])
    return ListingRepository(sessions)
