from __future__ import annotations

from dataclasses import dataclass

from lhf.scraper.onthemarket.json_values import (
    as_dict,
    as_display_price,
    as_int,
    as_joined_features,
    as_lat_lon,
    as_list,
    as_optional_str,
    extract_next_data,
    nested,
)
from lhf.scraper.onthemarket.shards import ORIGIN


@dataclass(frozen=True, slots=True)
class SearchCard:
    listing_id: str
    url: str
    display_address: str | None = None
    asking_price_gbp: int | None = None
    price_qualifier: str | None = None
    bedrooms: int | None = None
    bathrooms: int | None = None
    property_type: str | None = None
    tenure_type: str | None = None
    key_features: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    listing_update_reason: str | None = None


@dataclass(frozen=True, slots=True)
class SearchPage:
    properties: list[SearchCard]
    total_results: int


def parse_search_page(html: str) -> SearchPage:
    payload = extract_next_data(html, page="search page")
    results = nested(payload, "props", "initialReduxState", "results")
    if not isinstance(results, dict):
        raise ValueError("search page is missing results")
    raw = as_dict(results)
    total_results = _required_total_results(raw.get("totalResults"))
    cards: list[SearchCard] = []
    for item in as_list(raw.get("list")):
        card = _search_card(as_dict(item))
        if card is not None:
            cards.append(card)
    return SearchPage(properties=cards, total_results=total_results)


def _search_card(raw: dict[str, object]) -> SearchCard | None:
    listing_id = raw.get("id")
    if not isinstance(listing_id, str):
        return None
    identifier = listing_id.strip()
    if not identifier:
        return None
    url = _listing_url(as_optional_str(raw.get("details-url")), identifier)
    if url is None:
        return None
    latitude, longitude = as_lat_lon(raw.get("location"))
    features = raw.get("features")
    return SearchCard(
        listing_id=identifier,
        url=url,
        display_address=as_optional_str(raw.get("address")),
        asking_price_gbp=as_display_price(raw.get("price")),
        price_qualifier=as_optional_str(raw.get("price-qualifier")),
        bedrooms=as_int(raw.get("bedrooms")),
        bathrooms=as_int(raw.get("bathrooms")),
        property_type=as_optional_str(raw.get("humanised-property-type")),
        tenure_type=_tenure_from_features(features),
        key_features=as_joined_features(features),
        latitude=latitude,
        longitude=longitude,
        listing_update_reason=as_optional_str(raw.get("days-since-added-reduced")),
    )


def _listing_url(details_url: str | None, listing_id: str) -> str | None:
    if details_url is None:
        return f"{ORIGIN}/details/{listing_id}/"
    stripped = details_url.strip()
    if not stripped:
        return None
    if stripped.startswith(("http://", "https://")):
        return stripped
    return f"{ORIGIN}{stripped}"


def _tenure_from_features(features: object) -> str | None:
    for item in as_list(features):
        text = as_optional_str(item)
        if text is None or not text.lower().startswith("tenure:"):
            continue
        value = as_optional_str(text.split(":", 1)[1])
        if value is None or value.lower() == "ask agent":
            return None
        return value
    return None


def _required_total_results(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError("search page is missing totalResults")
    return value
