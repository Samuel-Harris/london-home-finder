from pathlib import Path

import pytest
from lhf.scraper.zoopla.detail import parse_property_data

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_property_data_reads_listing_data() -> None:
    detail = parse_property_data((FIXTURES / "detail.html").read_text(encoding="utf-8"))

    assert detail.display_address == "Waltham Road, Carshalton SM5"
    assert detail.asking_price_gbp == 450000
    assert detail.price_qualifier == "Offers over"
    assert detail.bedrooms == 3
    assert detail.bathrooms == 1
    assert detail.property_type == "terraced"
    assert detail.postcode == "SM5 1PN"
    assert detail.floor_area_sqft == 721
    assert detail.tenure_type == "FREEHOLD"
    assert detail.key_features is not None
    assert "Three bedroom mid terrace family home" in detail.key_features
    assert detail.description is not None
    assert "beautifully presented three-bedroom" in detail.description
    assert detail.garden is not None
    assert "garden" in detail.garden.lower()
    assert detail.parking is None
    assert detail.latitude == 51.380471
    assert detail.longitude == -0.173548
    assert detail.nearest_stations is not None
    assert detail.nearest_stations[0].name == "Hackbridge"
    assert detail.nearest_stations[0].distance == 0.9
    assert detail.nearest_stations[0].unit == "miles"
    assert detail.nearest_stations[1].name == "Carshalton"
    assert detail.nearest_stations[1].distance == 0.9
    assert detail.listing_update_reason == "Just added"
    assert detail.first_visible_date == "2026-08-30T11:55:02"


def test_parse_property_data_rejects_missing_payload() -> None:
    with pytest.raises(ValueError, match="missing __next_f"):
        parse_property_data("<html>no listing</html>")
