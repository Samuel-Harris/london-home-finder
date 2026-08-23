from pathlib import Path

from lhf.listings.listing import ListingDraft
from lhf.scraper.detail import PropertyDetail, parse_property_data
from lhf.scraper.map_listing import SQFT_PER_SQM, map_listing
from lhf.scraper.search import SearchCard, parse_search_page

FIXTURES = Path(__file__).parent / "fixtures"


def test_map_listing_keeps_poa_and_missing_postcode() -> None:
    draft = _mapped_draft("111111")

    assert draft.external_id == "111111"
    assert draft.source == "rightmove"
    assert draft.url == "https://www.rightmove.co.uk/properties/111111"
    assert draft.display_address == "12 Leasehold Lane, London"
    assert draft.asking_price_gbp is None
    assert draft.price_qualifier == "POA"
    assert draft.bedrooms == 2
    assert draft.postcode is None
    assert draft.floor_area_sqm == 58
    assert draft.tenure_type == "LEASEHOLD"
    assert draft.years_remaining_on_lease == 87
    assert draft.annual_service_charge_gbp == 2400
    assert draft.annual_ground_rent_gbp == 400


def test_map_listing_nulls_freehold_zero_lease_years() -> None:
    draft = _mapped_draft("222222")

    assert draft.external_id == "222222"
    assert draft.asking_price_gbp == 650_000
    assert draft.price_qualifier == "Guide Price"
    assert draft.bedrooms == 3
    assert draft.postcode == "SW1A 2AA"
    assert draft.floor_area_sqm == 700 / SQFT_PER_SQM
    assert draft.tenure_type == "FREEHOLD"
    assert draft.years_remaining_on_lease is None
    assert draft.annual_service_charge_gbp is None
    assert draft.annual_ground_rent_gbp is None


def test_map_listing_without_detail_uses_search_card() -> None:
    card = next(item for item in _search_cards() if item.listing_id == "222222")
    draft = map_listing(card, None)

    assert draft.asking_price_gbp == 650_000
    assert draft.display_address == "10 Downing Street, London"
    assert draft.floor_area_sqm == 65
    assert draft.postcode is None
    assert draft.years_remaining_on_lease is None


def test_map_listing_nulls_invalid_postcode() -> None:
    draft = map_listing(
        SearchCard(listing_id="1", url="https://www.rightmove.co.uk/properties/1"),
        PropertyDetail(outcode="XX", incode="YYY"),
    )

    assert draft.postcode is None


def _mapped_draft(external_id: str) -> ListingDraft:
    card = next(item for item in _search_cards() if item.listing_id == external_id)
    detail_name = "detail_leasehold.html" if external_id == "111111" else "detail_freehold.html"
    detail = parse_property_data((FIXTURES / detail_name).read_text(encoding="utf-8"))
    return map_listing(card, detail)


def _search_cards() -> list[SearchCard]:
    return parse_search_page((FIXTURES / "search.html").read_text(encoding="utf-8")).properties
