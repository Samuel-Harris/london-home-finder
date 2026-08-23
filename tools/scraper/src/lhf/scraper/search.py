from __future__ import annotations

import json
import re
from dataclasses import dataclass

from lhf.scraper.http import RIGHTMOVE_ORIGIN
from lhf.scraper.json_values import as_dict, as_int, as_list, as_optional_str, as_positive_int

_NEXT_DATA = re.compile(
    r'<script id="__NEXT_DATA__" type="application/json">\s*(.*?)\s*</script>',
    re.DOTALL,
)


@dataclass(frozen=True, slots=True)
class SearchCard:
    listing_id: str
    url: str
    display_address: str | None = None
    asking_price_gbp: int | None = None
    price_qualifier: str | None = None
    bedrooms: int | None = None
    display_size: str | None = None
    tenure_type: str | None = None


@dataclass(frozen=True, slots=True)
class SearchPage:
    properties: list[SearchCard]
    result_count: int | None


def parse_search_page(html: str) -> SearchPage:
    match = _NEXT_DATA.search(html)
    if match is None:
        return SearchPage(properties=[], result_count=None)
    payload: object = json.loads(match.group(1))
    search_results = as_dict(_nested(payload, "props", "pageProps", "searchResults"))
    cards: list[SearchCard] = []
    for item in as_list(search_results.get("properties")):
        card = _search_card(as_dict(item))
        if card is not None:
            cards.append(card)
    return SearchPage(
        properties=cards, result_count=_result_count(search_results.get("resultCount"))
    )


def _search_card(raw: dict[str, object]) -> SearchCard | None:
    listing_id = raw.get("id")
    if listing_id is None:
        return None
    identifier = str(listing_id)
    display_prices = as_list(raw.get("displayPrices"))
    qualifier = None
    if display_prices:
        qualifier = as_optional_str(as_dict(display_prices[0]).get("displayPriceQualifier"))
    return SearchCard(
        listing_id=identifier,
        url=_listing_url(as_optional_str(raw.get("propertyUrl")), identifier),
        display_address=as_optional_str(raw.get("displayAddress")),
        asking_price_gbp=as_positive_int(as_dict(raw.get("price")).get("amount")),
        price_qualifier=qualifier,
        bedrooms=as_int(raw.get("bedrooms")),
        display_size=as_optional_str(raw.get("displaySize")),
        tenure_type=as_optional_str(as_dict(raw.get("tenure")).get("tenureType")),
    )


def _listing_url(property_url: str | None, listing_id: str) -> str:
    if property_url is None:
        return f"{RIGHTMOVE_ORIGIN}/properties/{listing_id}"
    if property_url.startswith(("http://", "https://")):
        return property_url
    return f"{RIGHTMOVE_ORIGIN}{property_url}"


def _result_count(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value >= 0 else None
    if isinstance(value, str):
        digits = value.strip().replace(",", "")
        if digits.isdigit():
            return int(digits)
    return None


def _nested(payload: object, *keys: str) -> object:
    current: object = payload
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = as_dict(current).get(key)
    return current
