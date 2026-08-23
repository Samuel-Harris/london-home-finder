from pathlib import Path

from lhf.listings.listing import NearestStation
from lhf.scraper.search import parse_search_page

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_search_page_reads_next_data() -> None:
    page = parse_search_page((FIXTURES / "search.html").read_text(encoding="utf-8"))

    assert page.result_count == 2
    assert [item.listing_id for item in page.properties] == ["111111", "222222", "111111"]
    assert page.properties[0].asking_price_gbp is None
    assert page.properties[0].price_qualifier == "POA"
    assert page.properties[0].property_type == "flat"
    assert page.properties[0].property_sub_type == "Maisonette"
    assert page.properties[0].key_features == "Communal gardens"
    assert page.properties[0].description == "A maisonette somewhere."
    assert page.properties[0].bathrooms == 9
    assert page.properties[0].latitude == 51.0
    assert page.properties[0].longitude == 0.0
    assert page.properties[0].listing_update_reason == "Reduced on 12/05/2026"
    assert page.properties[0].listing_update_date == "2026-05-12T10:00:00Z"
    assert page.properties[0].first_visible_date == "2026-01-15T12:00:00Z"
    assert page.properties[1].asking_price_gbp == 650000
    assert page.properties[1].url == "https://www.rightmove.co.uk/properties/222222"
    assert page.properties[1].property_type == "house"
    assert page.properties[1].property_sub_type == "Terraced"
    assert page.properties[1].key_features == "Rear garden\nPeriod features"
    assert page.properties[1].description == "A terraced house in Westminster."
    assert page.properties[1].bathrooms == 2
    assert page.properties[1].latitude == 51.5
    assert page.properties[1].longitude == -0.12
    assert page.properties[1].listing_update_reason == "new"
    assert page.properties[1].listing_update_date == "2026-02-01T00:00:00Z"
    assert page.properties[1].first_visible_date == "2026-02-01T00:00:00Z"
    assert page.properties[1].nearest_stations == (
        NearestStation(
            name="Westminster Station",
            types=("LONDON_UNDERGROUND", "NATIONAL_TRAIN"),
            distance=0.15,
            unit="miles",
        ),
        NearestStation(
            name="St James's Park Station",
            types=("LONDON_UNDERGROUND",),
            distance=0.4,
            unit="miles",
        ),
        NearestStation(
            name="Waterloo Station",
            types=("NATIONAL_TRAIN", "LONDON_UNDERGROUND"),
            distance=0.9,
            unit="miles",
        ),
    )
    assert page.properties[2].property_type is None
    assert page.properties[2].property_sub_type is None
    assert page.properties[2].key_features is None
    assert page.properties[2].description is None


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
