from __future__ import annotations

from dataclasses import dataclass

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


def split_filter(search_filter: SearchFilter) -> tuple[SearchFilter, SearchFilter]:
    if search_filter.min_price < search_filter.max_price:
        mid_price = (search_filter.min_price + search_filter.max_price) // 2
        return (
            SearchFilter(
                min_price=search_filter.min_price,
                max_price=mid_price,
                min_bedrooms=search_filter.min_bedrooms,
                max_bedrooms=search_filter.max_bedrooms,
            ),
            SearchFilter(
                min_price=mid_price + 1,
                max_price=search_filter.max_price,
                min_bedrooms=search_filter.min_bedrooms,
                max_bedrooms=search_filter.max_bedrooms,
            ),
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
            SearchFilter(
                min_price=search_filter.min_price,
                max_price=search_filter.max_price,
                min_bedrooms=min_bedrooms,
                max_bedrooms=mid_bedrooms,
            ),
            SearchFilter(
                min_price=search_filter.min_price,
                max_price=search_filter.max_price,
                min_bedrooms=mid_bedrooms + 1,
                max_bedrooms=max_bedrooms,
            ),
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
    if index != 0:
        parts.append(f"index={index}")
    return "&".join(parts)
