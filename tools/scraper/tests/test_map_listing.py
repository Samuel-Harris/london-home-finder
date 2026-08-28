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
    assert draft.property_type == "flat"
    assert draft.property_sub_type == "Maisonette"
    assert draft.postcode is None
    assert draft.floor_area_sqm == 58
    assert draft.tenure_type == "LEASEHOLD"
    assert draft.years_remaining_on_lease == 87
    assert draft.annual_service_charge_gbp == 2400
    assert draft.annual_ground_rent_gbp == 400
    assert draft.key_features == "Private garden\nLift"
    assert draft.description == "A leasehold maisonette.<br /><br />Private garden."
    assert draft.bathrooms == 1
    assert draft.garden == "Yes"
    assert draft.parking == "Allocated underground"
    assert draft.latitude == 51.501
    assert draft.longitude == -0.1416
    assert draft.listing_update_reason == "Reduced on 12/05/2026"
    assert draft.listing_update_date == "2026-05-12T10:00:00Z"
    assert draft.first_visible_date == "2026-01-15T12:00:00Z"
    assert draft.nearest_stations is not None
    assert [station.name for station in draft.nearest_stations] == [
        "Westminster Station",
        "Waterloo Station",
    ]
    assert draft.nearest_stations[0].types == ("LONDON_UNDERGROUND", "NATIONAL_TRAIN")


def test_map_listing_nulls_freehold_zero_lease_years() -> None:
    draft = _mapped_draft("222222")

    assert draft.external_id == "222222"
    assert draft.asking_price_gbp == 650_000
    assert draft.price_qualifier == "Guide Price"
    assert draft.bedrooms == 3
    assert draft.property_type == "house"
    assert draft.property_sub_type == "Terraced"
    assert draft.postcode == "SW1A 2AA"
    assert draft.floor_area_sqm == 700 / SQFT_PER_SQM
    assert draft.tenure_type == "FREEHOLD"
    assert draft.years_remaining_on_lease is None
    assert draft.annual_service_charge_gbp is None
    assert draft.annual_ground_rent_gbp is None
    assert draft.key_features == "Rear garden\nPeriod features"
    assert draft.description == "A terraced house in Westminster."
    assert draft.bathrooms == 2
    assert draft.garden == "Private garden"
    assert draft.parking is None
    assert draft.latitude == 51.5034
    assert draft.longitude == -0.1276
    assert draft.first_visible_date == "2026-02-01T00:00:00Z"
    assert draft.listing_update_date == "2026-02-01T00:00:00Z"
    assert draft.listing_update_reason == "new"
    assert draft.nearest_stations is not None
    assert [station.name for station in draft.nearest_stations] == [
        "Westminster Station",
        "St James's Park Station",
        "Waterloo Station",
    ]


def test_map_listing_without_detail_uses_search_card() -> None:
    card = next(item for item in _search_cards() if item.listing_id == "222222")
    draft = map_listing(card, None)

    assert draft.asking_price_gbp == 650_000
    assert draft.display_address == "10 Downing Street, London"
    assert draft.floor_area_sqm == 65
    assert draft.property_type == "house"
    assert draft.property_sub_type == "Terraced"
    assert draft.key_features == "Rear garden\nPeriod features"
    assert draft.description == "A terraced house in Westminster."
    assert draft.postcode is None
    assert draft.years_remaining_on_lease is None
    assert draft.bathrooms == 2
    assert draft.latitude == 51.5
    assert draft.longitude == -0.12
    assert draft.nearest_stations is not None
    assert len(draft.nearest_stations) == 3


def test_map_listing_prefers_search_asking_price() -> None:
    draft = map_listing(
        SearchCard(
            listing_id="1",
            url="https://www.rightmove.co.uk/properties/1",
            asking_price_gbp=650_000,
        ),
        PropertyDetail(asking_price_gbp=700_000),
    )

    assert draft.asking_price_gbp == 650_000


def test_map_listing_prefers_detail_narrative_over_search() -> None:
    draft = map_listing(
        SearchCard(
            listing_id="1",
            url="https://www.rightmove.co.uk/properties/1",
            key_features="Communal gardens",
            description="Search summary.",
        ),
        PropertyDetail(
            key_features="Private garden\nLift",
            description="Detail description.",
        ),
    )

    assert draft.key_features == "Private garden\nLift"
    assert draft.description == "Detail description."


def test_map_listing_prefers_detail_property_type() -> None:
    draft = map_listing(
        SearchCard(
            listing_id="1",
            url="https://www.rightmove.co.uk/properties/1",
            property_type="house",
            property_sub_type="Terraced",
        ),
        PropertyDetail(property_type="flat", property_sub_type="Maisonette"),
    )

    assert draft.property_type == "flat"
    assert draft.property_sub_type == "Maisonette"


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
