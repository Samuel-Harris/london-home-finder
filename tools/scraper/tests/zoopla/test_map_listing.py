from pathlib import Path

import pytest
from lhf.scraper.zoopla.detail import parse_property_data
from lhf.scraper.zoopla.map_listing import SQFT_PER_SQM, map_listing
from lhf.scraper.zoopla.search import SearchCard, parse_search_page

FIXTURES = Path(__file__).parent / "fixtures"


def test_map_listing_prefers_detail_postcode_and_description() -> None:
    search = parse_search_page((FIXTURES / "search.html").read_text(encoding="utf-8")).properties[0]
    detail = parse_property_data((FIXTURES / "detail.html").read_text(encoding="utf-8"))
    draft = map_listing(search, detail)

    assert draft.source == "zoopla"
    assert draft.external_id == "74103170"
    assert draft.url == "https://www.zoopla.co.uk/for-sale/details/74103170/"
    assert draft.display_address == "Waltham Road, Carshalton SM5"
    assert draft.asking_price_gbp == 450000
    assert draft.postcode == "SM5 1PN"
    assert draft.floor_area_sqm == pytest.approx(721 / SQFT_PER_SQM)
    assert draft.tenure_type == "FREEHOLD"
    assert draft.years_remaining_on_lease is None
    assert draft.description is not None
    assert "beautifully presented three-bedroom" in draft.description
    assert draft.nearest_stations is not None
    assert draft.nearest_stations[0].name == "Hackbridge"


def test_map_listing_without_detail_uses_search_card() -> None:
    search = SearchCard(
        listing_id="1",
        url="https://www.zoopla.co.uk/for-sale/details/1/",
        display_address="Example Road",
        asking_price_gbp=400000,
        bedrooms=2,
        size_sqft=500,
        property_type="terraced",
        tenure_type="FREEHOLD",
        summary="A house.",
    )
    draft = map_listing(search, None)
    assert draft.postcode is None
    assert draft.asking_price_gbp == 400000
    assert draft.floor_area_sqm == pytest.approx(500 / SQFT_PER_SQM)
    assert draft.description == "A house."
    assert draft.nearest_stations is None
