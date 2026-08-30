from __future__ import annotations

from dataclasses import dataclass, replace

from lhf.scraper.zoopla.http import ZOOPLA_ORIGIN

HOUSES_SEARCH_PATH = "/for-sale/houses/london/"
PROPERTY_SEARCH_PATH = "/for-sale/property/london/"
UNBOUNDED_MAX_BEDROOMS = 20


@dataclass(frozen=True, slots=True)
class SearchFilter:
    min_price: int
    max_price: int
    min_bedrooms: int | None = None
    max_bedrooms: int | None = None
    property_types: tuple[str, ...] | None = None
    tenure: str | None = None


def split_filter(search_filter: SearchFilter) -> tuple[SearchFilter, SearchFilter]:
    if search_filter.min_price < search_filter.max_price:
        mid_price = (search_filter.min_price + search_filter.max_price) // 2
        return (
            replace(search_filter, max_price=mid_price),
            replace(search_filter, min_price=mid_price + 1),
        )
    min_bedrooms = search_filter.min_bedrooms if search_filter.min_bedrooms is not None else 0
    max_bedrooms = (
        search_filter.max_bedrooms
        if search_filter.max_bedrooms is not None
        else UNBOUNDED_MAX_BEDROOMS
    )
    if min_bedrooms < max_bedrooms:
        mid_bedrooms = (min_bedrooms + max_bedrooms) // 2
        return (
            replace(search_filter, min_bedrooms=min_bedrooms, max_bedrooms=mid_bedrooms),
            replace(search_filter, min_bedrooms=mid_bedrooms + 1, max_bedrooms=max_bedrooms),
        )
    raise ValueError(
        "cannot split search filter "
        f"min_price={search_filter.min_price} max_price={search_filter.max_price} "
        f"min_bedrooms={min_bedrooms} max_bedrooms={max_bedrooms}"
    )


def search_path(search_filter: SearchFilter) -> str:
    path = HOUSES_SEARCH_PATH if search_filter.property_types else PROPERTY_SEARCH_PATH
    return f"{ZOOPLA_ORIGIN}{path}"


def search_url(search_filter: SearchFilter, page_number: int) -> str:
    return f"{search_path(search_filter)}?{_filter_query(search_filter)}&pn={page_number}"


def _filter_query(search_filter: SearchFilter) -> str:
    parts = [
        f"price_min={search_filter.min_price}",
        f"price_max={search_filter.max_price}",
    ]
    if search_filter.min_bedrooms is not None:
        parts.append(f"beds_min={search_filter.min_bedrooms}")
    if search_filter.max_bedrooms is not None:
        parts.append(f"beds_max={search_filter.max_bedrooms}")
    if search_filter.tenure is not None:
        parts.append(f"tenure={search_filter.tenure.lower()}")
    return "&".join(parts)


def filter_label(search_filter: SearchFilter) -> str:
    return " ".join(_filter_query(search_filter).split("&"))
