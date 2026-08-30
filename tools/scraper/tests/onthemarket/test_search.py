from pathlib import Path

import pytest
from lhf.scraper.onthemarket.search import parse_search_page

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_search_page_reads_cards_and_drops_integer_ads() -> None:
    page = parse_search_page((FIXTURES / "search-houses.html").read_text(encoding="utf-8"))

    assert page.total_results == 22660
    listing_ids = [card.listing_id for card in page.properties]
    assert "19924482" in listing_ids
    assert "20226126" in listing_ids
    assert 1689 not in listing_ids
    assert "1689" not in listing_ids
    assert 1567 not in listing_ids
    assert all(isinstance(listing_id, str) for listing_id in listing_ids)
    assert len(page.properties) == 28

    card = next(item for item in page.properties if item.listing_id == "19924482")
    assert card.url == "https://www.onthemarket.com/details/19924482/"
    assert card.display_address == "Wakefield Street, East Ham, London, E6"
    assert card.asking_price_gbp == 650_000
    assert card.bedrooms == 3
    assert card.bathrooms == 3
    assert card.property_type == "Terraced house"
    assert card.tenure_type == "Freehold"
    assert card.latitude == 51.533527
    assert card.longitude == 0.045418
    assert card.listing_update_reason == "Added > 14 days"


def test_parse_search_page_reads_next_data_with_extra_script_attributes() -> None:
    html = (
        '<script id="__NEXT_DATA__" type="application/json" crossorigin="anonymous">'
        '{"props":{"initialReduxState":{"results":{"totalResults":0,"list":[]}}}}'
        "</script>"
    )
    page = parse_search_page(html)
    assert page.total_results == 0
    assert page.properties == []


def test_parse_search_page_rejects_missing_embed() -> None:
    with pytest.raises(ValueError, match="missing __NEXT_DATA__"):
        parse_search_page("<html>couldn't find properties</html>")


def test_parse_search_page_rejects_missing_results() -> None:
    html = (
        '<script id="__NEXT_DATA__" type="application/json">'
        '{"props":{"initialReduxState":{}}}</script>'
    )
    with pytest.raises(ValueError, match="missing results"):
        parse_search_page(html)


def test_parse_search_page_rejects_missing_total_results() -> None:
    html = (
        '<script id="__NEXT_DATA__" type="application/json">'
        '{"props":{"initialReduxState":{"results":{"list":[]}}}}'
        "</script>"
    )
    with pytest.raises(ValueError, match="missing totalResults"):
        parse_search_page(html)
