from pathlib import Path

import pytest
from lhf.scraper.zoopla.search import parse_search_page

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_search_page_reads_regular_listings() -> None:
    page = parse_search_page((FIXTURES / "search.html").read_text(encoding="utf-8"))

    assert page.result_count == 11007
    assert page.page_number == 1
    assert page.page_number_max == 40
    assert len(page.properties) == 25
    first = page.properties[0]
    assert first.listing_id == "74103170"
    assert first.url == "https://www.zoopla.co.uk/for-sale/details/74103170/"
    assert first.display_address == "Waltham Road, Carshalton SM5"
    assert first.asking_price_gbp == 450000
    assert first.price_qualifier == "Offers over"
    assert first.bedrooms == 3
    assert first.bathrooms == 1
    assert first.property_type == "terraced"
    assert first.tenure_type == "FREEHOLD"
    assert first.size_sqft == 721
    assert first.latitude == 51.380471
    assert first.longitude == -0.173548
    ids = [card.listing_id for card in page.properties]
    assert len(ids) == len(set(ids))
    chain_free = next(card for card in page.properties if card.listing_id == "74102924")
    assert chain_free.tenure_type == "FREEHOLD"


def test_parse_search_page_rejects_missing_payload() -> None:
    with pytest.raises(ValueError, match="missing __next_f"):
        parse_search_page("<html>couldn't find properties</html>")
