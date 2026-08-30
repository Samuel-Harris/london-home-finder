from pathlib import Path

from lhf.listings.listing import ListingDraft
from lhf.scraper.onthemarket.detail import parse_detail_page
from lhf.scraper.onthemarket.in_window import in_window
from lhf.scraper.onthemarket.map_listing import map_listing
from lhf.scraper.onthemarket.search import SearchCard, parse_search_page
from lhf.scraper.window import DEFAULT_WINDOW, IngestWindow

FIXTURES = Path(__file__).parent / "fixtures"


def test_map_listing_sets_onthemarket_source() -> None:
    draft = _mapped_draft("19924482")

    assert draft.source == "onthemarket"
    assert draft.external_id == "19924482"
    assert draft.url == "https://www.onthemarket.com/details/19924482/"
    assert draft.asking_price_gbp == 650_000
    assert draft.postcode == "E6 1LG"
    assert draft.tenure_type == "Freehold"
    assert draft.property_type == "Terraced house"
    assert draft.property_sub_type == "terraced"


def test_in_window_drops_known_leasehold() -> None:
    draft = ListingDraft(
        source="onthemarket",
        external_id="1",
        url="https://www.onthemarket.com/details/1/",
        asking_price_gbp=500_000,
        bedrooms=3,
        property_type="Terraced house",
        tenure_type="Leasehold",
    )
    assert in_window(draft, DEFAULT_WINDOW) is False


def test_in_window_drops_out_of_band_price() -> None:
    draft = ListingDraft(
        source="onthemarket",
        external_id="1",
        url="https://www.onthemarket.com/details/1/",
        asking_price_gbp=200_000,
        bedrooms=3,
        property_type="Terraced house",
        tenure_type="Freehold",
    )
    assert in_window(draft, DEFAULT_WINDOW) is False


def test_in_window_keeps_poa_and_unknown_tenure() -> None:
    poa = ListingDraft(
        source="onthemarket",
        external_id="1",
        url="https://www.onthemarket.com/details/1/",
        asking_price_gbp=None,
        bedrooms=3,
        property_type="Terraced house",
        tenure_type="Freehold",
    )
    unknown = ListingDraft(
        source="onthemarket",
        external_id="2",
        url="https://www.onthemarket.com/details/2/",
        asking_price_gbp=500_000,
        bedrooms=3,
        property_type="Terraced house",
        tenure_type=None,
    )
    assert in_window(poa, DEFAULT_WINDOW) is True
    assert in_window(unknown, DEFAULT_WINDOW) is True


def test_in_window_keeps_ask_agent_mapped_draft() -> None:
    card = SearchCard(
        listing_id="20226126",
        url="https://www.onthemarket.com/details/20226126/",
        asking_price_gbp=550_000,
        bedrooms=5,
        property_type="Semi-detached house",
        tenure_type=None,
    )
    detail = parse_detail_page((FIXTURES / "detail-20226126.html").read_text(encoding="utf-8"))
    draft = map_listing(card, detail)
    assert draft.tenure_type is None
    assert in_window(draft, DEFAULT_WINDOW) is True


def test_in_window_uses_custom_bounds() -> None:
    draft = ListingDraft(
        source="onthemarket",
        external_id="1",
        url="https://www.onthemarket.com/details/1/",
        asking_price_gbp=900_000,
        bedrooms=2,
        tenure_type="Freehold",
    )
    assert in_window(draft, IngestWindow(min_price=800_000, max_price=1_000_000)) is True


def test_in_window_keeps_end_of_terrace_and_generic_house() -> None:
    terrace = ListingDraft(
        source="onthemarket",
        external_id="1",
        url="https://www.onthemarket.com/details/1/",
        asking_price_gbp=500_000,
        bedrooms=3,
        property_type="End of terrace house",
        tenure_type="Freehold",
    )
    house = ListingDraft(
        source="onthemarket",
        external_id="2",
        url="https://www.onthemarket.com/details/2/",
        asking_price_gbp=650_000,
        bedrooms=3,
        property_type="House",
        tenure_type="Freehold",
    )
    flat = ListingDraft(
        source="onthemarket",
        external_id="3",
        url="https://www.onthemarket.com/details/3/",
        asking_price_gbp=500_000,
        bedrooms=3,
        property_type="Flat",
        tenure_type="Freehold",
    )
    assert in_window(terrace, DEFAULT_WINDOW) is True
    assert in_window(house, DEFAULT_WINDOW) is True
    assert in_window(flat, DEFAULT_WINDOW) is False


def test_in_window_prefers_property_sub_type() -> None:
    draft = ListingDraft(
        source="onthemarket",
        external_id="1",
        url="https://www.onthemarket.com/details/1/",
        asking_price_gbp=500_000,
        bedrooms=3,
        property_type="House",
        property_sub_type="terraced",
        tenure_type="Freehold",
    )
    assert in_window(draft, DEFAULT_WINDOW) is True


def _mapped_draft(external_id: str) -> ListingDraft:
    card = next(item for item in _search_cards() if item.listing_id == external_id)
    detail = parse_detail_page(
        (FIXTURES / f"detail-{external_id}.html").read_text(encoding="utf-8")
    )
    return map_listing(card, detail)


def _search_cards() -> list[SearchCard]:
    html = (FIXTURES / "search-houses.html").read_text(encoding="utf-8")
    return parse_search_page(html).properties
