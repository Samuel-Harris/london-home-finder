import pytest
from lhf.scraper.onthemarket.shards import (
    LONDON_LOCAL_AUTHORITIES,
    ORIGIN,
    UNBOUNDED_MAX_BEDROOMS,
    ShardFilter,
    filter_label,
    houses_spine,
    search_url,
    split_shard,
    window_property_kinds,
)
from lhf.scraper.window import DEFAULT_WINDOW, IngestWindow

_FORBIDDEN = ("min-price", "max-price", "min-bedrooms", "prop-types")


def test_search_url_is_path_only_and_omits_robots_query_keys() -> None:
    shard = ShardFilter(bedrooms=2, property_kind="houses", location="london")
    page_one = search_url(shard, 1)
    page_two = search_url(shard, 2)

    assert page_one == f"{ORIGIN}/for-sale/2-bed-houses/london/"
    assert page_two == f"{ORIGIN}/for-sale/2-bed-houses/london/?page=2"
    for url in (page_one, page_two):
        for forbidden in _FORBIDDEN:
            assert forbidden not in url


def test_search_url_rejects_page_below_one() -> None:
    with pytest.raises(ValueError, match="page must be at least 1"):
        search_url(ShardFilter(bedrooms=2, property_kind="houses", location="london"), 0)


def test_shard_filter_requires_at_least_one_bedroom() -> None:
    with pytest.raises(ValueError, match="bedrooms must be >= 1"):
        ShardFilter(bedrooms=0, property_kind="houses", location="london")


def test_shard_filter_rejects_unknown_location() -> None:
    with pytest.raises(ValueError, match="unknown location slug"):
        ShardFilter(bedrooms=2, property_kind="houses", location="not-a-borough")


def test_split_houses_emits_window_kinds_then_london_splits_to_boroughs() -> None:
    houses = ShardFilter(bedrooms=3, property_kind="houses", location="london")
    kinds = split_shard(houses, DEFAULT_WINDOW)
    assert [shard.property_kind for shard in kinds] == [
        "detached",
        "semi-detached",
        "terraced",
        "bungalows",
    ]
    assert all(shard.bedrooms == 3 and shard.location == "london" for shard in kinds)

    terraced = kinds[2]
    boroughs = split_shard(terraced, DEFAULT_WINDOW)
    assert len(boroughs) == 33
    assert [shard.location for shard in boroughs] == list(LONDON_LOCAL_AUTHORITIES)
    assert all(shard.property_kind == "terraced" and shard.bedrooms == 3 for shard in boroughs)


def test_split_borough_is_unsplittable() -> None:
    with pytest.raises(ValueError, match="unsplittable"):
        split_shard(
            ShardFilter(bedrooms=3, property_kind="terraced", location="croydon"),
            DEFAULT_WINDOW,
        )


def test_bungalow_window_type_maps_to_bungalows_path() -> None:
    kinds = window_property_kinds(IngestWindow(property_types=("bungalow",), tenure=None))
    assert kinds == ("bungalows",)
    url = search_url(ShardFilter(bedrooms=2, property_kind="bungalows", location="london"), 1)
    assert url == f"{ORIGIN}/for-sale/2-bed-bungalows/london/"
    assert "bungalow/" not in url
    for forbidden in _FORBIDDEN:
        assert forbidden not in url


def test_houses_spine_seeds_from_min_bedrooms() -> None:
    spine = houses_spine(2)
    assert spine[0] == ShardFilter(bedrooms=2, property_kind="houses", location="london")
    assert spine[-1] == ShardFilter(
        bedrooms=UNBOUNDED_MAX_BEDROOMS, property_kind="houses", location="london"
    )
    assert [shard.bedrooms for shard in spine] == list(range(2, UNBOUNDED_MAX_BEDROOMS + 1))
    assert houses_spine(None)[0].bedrooms == 1
    assert houses_spine(0)[0].bedrooms == 1


def test_filter_label_names_the_path() -> None:
    assert (
        filter_label(ShardFilter(bedrooms=2, property_kind="houses", location="london"))
        == "2-bed-houses/london"
    )
