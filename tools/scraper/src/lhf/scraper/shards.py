from __future__ import annotations

from dataclasses import dataclass, replace

SEARCH_URL = (
    "https://www.rightmove.co.uk/property-for-sale/find.html"
    "?locationIdentifier=REGION%5E87490&channel=BUY&transactionType=BUY"
)
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


def search_url(search_filter: SearchFilter, index: int) -> str:
    parts = [
        SEARCH_URL,
        f"minPrice={search_filter.min_price}",
        f"maxPrice={search_filter.max_price}",
    ]
    if search_filter.min_bedrooms is not None:
        parts.append(f"minBedrooms={search_filter.min_bedrooms}")
    if search_filter.max_bedrooms is not None:
        parts.append(f"maxBedrooms={search_filter.max_bedrooms}")
    if search_filter.property_types:
        parts.append(f"propertyTypes={','.join(search_filter.property_types)}")
    if search_filter.tenure is not None:
        parts.append(f"tenureTypes={search_filter.tenure}")
    if index != 0:
        parts.append(f"index={index}")
    return "&".join(parts)
