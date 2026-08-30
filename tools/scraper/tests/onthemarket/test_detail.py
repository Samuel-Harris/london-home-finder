from pathlib import Path

from lhf.scraper.onthemarket.detail import parse_detail_page

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_detail_page_reads_price_postcode_and_freehold() -> None:
    detail = parse_detail_page((FIXTURES / "detail-19924482.html").read_text(encoding="utf-8"))

    assert detail.listing_id == "19924482"
    assert detail.url == "https://www.onthemarket.com/details/19924482/"
    assert detail.asking_price_gbp == 650_000
    assert detail.postcode == "E6 1LG"
    assert detail.tenure_type == "Freehold"
    assert detail.property_type == "Terraced house"
    assert detail.property_sub_type == "terraced"
    assert detail.bedrooms == 3
    assert detail.bathrooms == 3
    assert [station.name for station in detail.nearest_stations or ()][:2] == [
        "Upton Park Underground",
        "East Ham Underground",
    ]
    assert detail.nearest_stations is not None
    assert detail.nearest_stations[0].distance == 0.5
    assert detail.nearest_stations[0].unit == "mi"
    assert detail.nearest_stations[0].types == ("Tube",)


def test_parse_detail_page_nulls_ask_agent_tenure() -> None:
    detail = parse_detail_page((FIXTURES / "detail-20226126.html").read_text(encoding="utf-8"))

    assert detail.listing_id == "20226126"
    assert detail.asking_price_gbp == 550_000
    assert detail.postcode == "CR4 3EY"
    assert detail.tenure_type is None
