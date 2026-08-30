from __future__ import annotations

from lhf.listings.listing import ListingDraft
from lhf.scraper.onthemarket.search import SearchCard
from lhf.scraper.onthemarket.shards import WINDOW_TYPE_TO_KIND, window_property_kinds
from lhf.scraper.window import IngestWindow


def in_window(item: SearchCard | ListingDraft, window: IngestWindow) -> bool:
    if item.asking_price_gbp is not None and not (
        window.min_price <= item.asking_price_gbp <= window.max_price
    ):
        return False
    if (
        window.min_bedrooms is not None
        and item.bedrooms is not None
        and item.bedrooms < window.min_bedrooms
    ):
        return False
    if (
        window.tenure is not None
        and item.tenure_type is not None
        and item.tenure_type.casefold() != window.tenure.casefold()
    ):
        return False
    if window.property_types is None:
        return True
    sub_type = item.property_sub_type if isinstance(item, ListingDraft) else None
    return _property_type_in_window(item.property_type, sub_type, window)


def _property_type_in_window(
    property_type: str | None, property_sub_type: str | None, window: IngestWindow
) -> bool:
    allowed = window_property_kinds(window)
    if property_sub_type is not None:
        key = _normalise_type(property_sub_type)
        if key == "terrace":
            key = "terraced"
        mapped = WINDOW_TYPE_TO_KIND.get(key)
        if mapped is not None:
            return mapped in allowed
    if property_type is None:
        return True
    normalised = _normalise_type(property_type)
    for wanted in window.property_types or ():
        wanted_norm = _normalise_type(wanted)
        if wanted_norm == "detached" and "semi-detached" in normalised:
            continue
        if wanted_norm in normalised:
            return True
        if wanted_norm == "terraced" and "terrace" in normalised:
            return True
    return normalised == "house"


def _normalise_type(value: str) -> str:
    return value.casefold().replace("_", "-").replace(" ", "-")
