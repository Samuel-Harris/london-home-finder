from pathlib import Path
from typing import cast

from fastapi.testclient import TestClient
from httpx import Client
from lhf.api.app import create_app
from lhf.db.session import create_session_factory
from lhf.db_app.migrations import upgrade_database
from lhf.listings.listing import ListingDraft
from lhf.listings.listing_repository import ListingRepository


def test_health_endpoint_does_not_require_database_access(tmp_path: Path) -> None:
    test_client = cast(Client, TestClient(create_app(tmp_path / "not-created.sqlite3")))
    with test_client as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_listings_endpoint_reads_the_listings_repository(tmp_path: Path) -> None:
    database_path = tmp_path / "api.sqlite3"
    upgrade_database(database_path)
    repository = ListingRepository(create_session_factory(database_path))
    repository.upsert(
        [
            ListingDraft(
                source="example",
                external_id="home-1",
                title="A Westminster flat",
                asking_price_gbp=650_000,
                postcode="SW1A 1AA",
                url="https://example.test/home-1",
                floor_area_sqm=65,
            )
        ]
    )

    test_client = cast(Client, TestClient(create_app(database_path)))
    with test_client as client:
        response = client.get("/listings")

    assert response.status_code == 200
    assert response.json()[0]["external_id"] == "home-1"
    assert response.json()[0]["postcode"] == "SW1A 1AA"
