from __future__ import annotations

from dataclasses import dataclass

from lhf.scraper.zoopla.flight import concat_next_f, decode_json_field
from lhf.scraper.zoopla.http import ZOOPLA_ORIGIN
from lhf.scraper.zoopla.json_values import (
    as_dict,
    as_int,
    as_list,
    as_number,
    as_numeric_int,
    as_optional_str,
    as_positive_number,
    as_tenure_label,
)


@dataclass(frozen=True, slots=True)
class SearchCard:
    listing_id: str
    url: str
    display_address: str | None = None
    asking_price_gbp: int | None = None
    price_qualifier: str | None = None
    bedrooms: int | None = None
    bathrooms: int | None = None
    size_sqft: float | None = None
    property_type: str | None = None
    tenure_type: str | None = None
    summary: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    listing_update_reason: str | None = None
    first_visible_date: str | None = None


@dataclass(frozen=True, slots=True)
class SearchPage:
    properties: list[SearchCard]
    result_count: int | None
    page_number: int | None
    page_number_max: int | None


def parse_search_page(html: str) -> SearchPage:
    flight = concat_next_f(html)
    listings = decode_json_field(flight, "regularListingsFormatted")
    cards: list[SearchCard] = []
    for item in as_list(listings):
        card = _search_card(as_dict(item))
        if card is not None:
            cards.append(card)
    pagination = as_dict(decode_json_field(flight, "pagination"))
    return SearchPage(
        properties=cards,
        result_count=as_int(pagination.get("totalResults")),
        page_number=as_int(pagination.get("pageNumber")),
        page_number_max=as_int(pagination.get("pageNumberMax")),
    )


def _search_card(raw: dict[str, object]) -> SearchCard | None:
    listing_id = as_optional_str(raw.get("listingId"))
    if listing_id is None:
        return None
    uris = as_dict(raw.get("listingUris"))
    path = as_optional_str(uris.get("detail")) or f"/for-sale/details/{listing_id}/"
    pos = as_dict(raw.get("pos"))
    return SearchCard(
        listing_id=listing_id,
        url=_absolute_url(path),
        display_address=as_optional_str(raw.get("address")),
        asking_price_gbp=as_numeric_int(raw.get("priceUnformatted")),
        price_qualifier=as_optional_str(raw.get("priceTitle")),
        bedrooms=_feature_count(raw, "bed"),
        bathrooms=_feature_count(raw, "bath"),
        size_sqft=as_positive_number(raw.get("sizeSqft")),
        property_type=as_optional_str(raw.get("propertyType")),
        tenure_type=_tenure_from_tags(raw.get("tags")),
        summary=as_optional_str(raw.get("summaryDescription")),
        latitude=as_number(pos.get("lat")),
        longitude=as_number(pos.get("lng")),
        listing_update_reason=as_optional_str(raw.get("flag")),
        first_visible_date=as_optional_str(raw.get("publishedOn")),
    )


def _feature_count(raw: dict[str, object], icon_id: str) -> int | None:
    for item in as_list(raw.get("features")):
        feature = as_dict(item)
        if as_optional_str(feature.get("iconId")) != icon_id:
            continue
        return as_int(feature.get("content"))
    return None


def _tenure_from_tags(value: object) -> str | None:
    for item in as_list(value):
        tenure = as_tenure_label(as_dict(item).get("content"))
        if tenure is not None:
            return tenure
    return None


def _absolute_url(path: str) -> str:
    if path.startswith("http://") or path.startswith("https://"):
        return path
    return f"{ZOOPLA_ORIGIN}{path}"
