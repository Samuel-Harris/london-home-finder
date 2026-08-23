from pathlib import Path

from lhf.scraper.search import parse_search_page

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_search_page_reads_next_data() -> None:
    page = parse_search_page((FIXTURES / "search.html").read_text(encoding="utf-8"))

    assert page.result_count == 2
    assert [item.listing_id for item in page.properties] == ["111111", "222222", "111111"]
    assert page.properties[0].asking_price_gbp is None
    assert page.properties[0].price_qualifier == "POA"
    assert page.properties[1].asking_price_gbp == 650000
    assert page.properties[1].url == "https://www.rightmove.co.uk/properties/222222"


def test_parse_search_page_treats_missing_payload_as_empty() -> None:
    page = parse_search_page("<html>couldn't find properties</html>")

    assert page.properties == []
    assert page.result_count is None


def test_parse_search_page_reads_comma_formatted_result_count() -> None:
    html = (
        '<script id="__NEXT_DATA__" type="application/json">'
        '{"props":{"pageProps":{"searchResults":{"resultCount":"1,008","properties":[]}}}}'
        "</script>"
    )

    assert parse_search_page(html).result_count == 1008
