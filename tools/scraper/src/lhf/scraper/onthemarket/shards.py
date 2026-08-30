from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from lhf.scraper.window import IngestWindow

type PropertyKind = Literal["houses", "detached", "semi-detached", "terraced", "bungalows"]

UNBOUNDED_MAX_BEDROOMS = 20
PAGE_SIZE = 30
LAST_WORKING_PAGE = 34
PAGE_RESULT_CAP = 1020
ORIGIN = "https://www.onthemarket.com"

LONDON_LOCAL_AUTHORITIES: tuple[str, ...] = (
    "barking-and-dagenham",
    "barnet",
    "bexley",
    "brent",
    "bromley",
    "camden",
    "city-of-london",
    "croydon",
    "ealing",
    "enfield",
    "greenwich",
    "hackney",
    "hammersmith-and-fulham",
    "haringey",
    "harrow",
    "havering",
    "hillingdon",
    "hounslow",
    "islington",
    "kensington-and-chelsea",
    "kingston-upon-thames",
    "lambeth",
    "lewisham",
    "merton",
    "newham",
    "redbridge",
    "richmond-upon-thames",
    "southwark",
    "sutton",
    "tower-hamlets",
    "waltham-forest",
    "wandsworth",
    "westminster",
)

WINDOW_TYPE_TO_KIND: dict[str, PropertyKind] = {
    "detached": "detached",
    "semi-detached": "semi-detached",
    "terraced": "terraced",
    "bungalow": "bungalows",
}

_DEFAULT_KINDS: tuple[PropertyKind, ...] = (
    "detached",
    "semi-detached",
    "terraced",
    "bungalows",
)


@dataclass(frozen=True, slots=True)
class ShardFilter:
    bedrooms: int
    property_kind: PropertyKind
    location: str

    def __post_init__(self) -> None:
        if self.bedrooms < 1:
            raise ValueError("bedrooms must be >= 1")
        if self.location != "london" and self.location not in LONDON_LOCAL_AUTHORITIES:
            raise ValueError(f"unknown location slug: {self.location}")


def search_url(shard: ShardFilter, page: int) -> str:
    if page < 1:
        raise ValueError("page must be at least 1")
    path = f"{ORIGIN}/for-sale/{shard.bedrooms}-bed-{shard.property_kind}/{shard.location}/"
    if page == 1:
        return path
    return f"{path}?page={page}"


def detail_url(listing_id: str) -> str:
    return f"{ORIGIN}/details/{listing_id}/"


def split_shard(shard: ShardFilter, window: IngestWindow) -> tuple[ShardFilter, ...]:
    if shard.property_kind == "houses":
        return tuple(
            ShardFilter(
                bedrooms=shard.bedrooms,
                property_kind=kind,
                location=shard.location,
            )
            for kind in window_property_kinds(window)
        )
    if shard.location == "london":
        return tuple(
            ShardFilter(
                bedrooms=shard.bedrooms,
                property_kind=shard.property_kind,
                location=slug,
            )
            for slug in LONDON_LOCAL_AUTHORITIES
        )
    raise ValueError(f"cannot split unsplittable shard {filter_label(shard)}")


def houses_spine(min_bedrooms: int | None) -> tuple[ShardFilter, ...]:
    start = 1 if min_bedrooms is None or min_bedrooms < 1 else min_bedrooms
    return tuple(
        ShardFilter(bedrooms=bedrooms, property_kind="houses", location="london")
        for bedrooms in range(start, UNBOUNDED_MAX_BEDROOMS + 1)
    )


def filter_label(shard: ShardFilter) -> str:
    return f"{shard.bedrooms}-bed-{shard.property_kind}/{shard.location}"


def window_property_kinds(window: IngestWindow) -> tuple[PropertyKind, ...]:
    if window.property_types is None:
        return _DEFAULT_KINDS
    kinds: list[PropertyKind] = []
    seen: set[PropertyKind] = set()
    for raw in window.property_types:
        mapped = WINDOW_TYPE_TO_KIND.get(raw.lower())
        if mapped is None:
            raise ValueError(f"unknown property type {raw!r}")
        if mapped in seen:
            continue
        seen.add(mapped)
        kinds.append(mapped)
    if not kinds:
        raise ValueError("property_types must map to at least one OnTheMarket kind")
    return tuple(kinds)
