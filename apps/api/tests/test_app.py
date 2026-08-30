from pathlib import Path
from typing import cast

from fastapi.testclient import TestClient
from httpx import Client
from lhf.api.app import create_app
from lhf.db.session import create_session_factory
from lhf.db_app.migrations import upgrade_database
from lhf.listings.listing import ListingDraft, NearestStation
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
    repository.replace_source(
        "rightmove",
        [
            ListingDraft(
                source="rightmove",
                external_id="poa-1",
                url="https://www.rightmove.co.uk/properties/1",
                display_address=None,
                asking_price_gbp=None,
                price_qualifier="POA",
                bedrooms=2,
                property_type="flat",
                property_sub_type="Maisonette",
                postcode=None,
                floor_area_sqm=None,
                tenure_type="LEASEHOLD",
                years_remaining_on_lease=87,
                annual_service_charge_gbp=2400,
                annual_ground_rent_gbp=400,
                key_features="Private garden\nLift",
                description="A leasehold maisonette with a garden.",
                bathrooms=1,
                garden="Yes",
                parking="Allocated underground",
                latitude=51.501,
                longitude=-0.1416,
                nearest_stations=(
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
                ),
                listing_update_reason="Reduced on 12/05/2026",
                listing_update_date="2026-05-12T10:00:00Z",
                first_visible_date="2026-01-15T12:00:00Z",
            )
        ],
    )

    test_client = cast(Client, TestClient(create_app(database_path)))
    with test_client as client:
        response = client.get("/listings")

    assert response.status_code == 200
    listing = response.json()[0]
    assert listing["external_id"] == "poa-1"
    assert listing["display_address"] is None
    assert listing["asking_price_gbp"] is None
    assert listing["price_qualifier"] == "POA"
    assert listing["bedrooms"] == 2
    assert listing["property_type"] == "flat"
    assert listing["property_sub_type"] == "Maisonette"
    assert listing["postcode"] is None
    assert listing["tenure_type"] == "LEASEHOLD"
    assert listing["years_remaining_on_lease"] == 87
    assert listing["annual_service_charge_gbp"] == 2400
    assert listing["annual_ground_rent_gbp"] == 400
    assert listing["key_features"] == "Private garden\nLift"
    assert listing["description"] == "A leasehold maisonette with a garden."
    assert listing["bathrooms"] == 1
    assert listing["garden"] == "Yes"
    assert listing["parking"] == "Allocated underground"
    assert listing["latitude"] == 51.501
    assert listing["longitude"] == -0.1416
    assert listing["nearest_stations"] == [
        {
            "name": "Westminster Station",
            "types": ["LONDON_UNDERGROUND", "NATIONAL_TRAIN"],
            "distance": 0.15,
            "unit": "miles",
        },
        {
            "name": "Waterloo Station",
            "types": ["NATIONAL_TRAIN"],
            "distance": 0.8,
            "unit": "miles",
        },
    ]
    assert listing["listing_update_reason"] == "Reduced on 12/05/2026"
    assert listing["listing_update_date"] == "2026-05-12T10:00:00Z"
    assert listing["first_visible_date"] == "2026-01-15T12:00:00Z"
