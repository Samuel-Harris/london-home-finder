import json
from pathlib import Path

import pytest
from lhf_scraper.fixture import load_fixture


def test_load_fixture_builds_validated_listing_drafts(tmp_path: Path) -> None:
    fixture_path = tmp_path / "listings.json"
    fixture_path.write_text(
        json.dumps(
            [
                {
                    "source": "example",
                    "external_id": "home-1",
                    "title": "A Westminster flat",
                    "asking_price_gbp": 650000,
                    "postcode": "sw1a1aa",
                    "url": "https://example.test/home-1",
                    "floor_area_sqm": 65,
                }
            ]
        ),
        encoding="utf-8",
    )

    listings = load_fixture(fixture_path)

    assert len(listings) == 1
    assert listings[0].postcode == "SW1A 1AA"
    assert listings[0].floor_area_sqm == 65


def test_load_fixture_rejects_a_non_array_document(tmp_path: Path) -> None:
    fixture_path = tmp_path / "listings.json"
    fixture_path.write_text("{}", encoding="utf-8")

    with pytest.raises(ValueError, match="fixture root must be a JSON array"):
        load_fixture(fixture_path)
