import pytest
from lhf.scraper.zoopla.http import ZOOPLA_ORIGIN
from lhf.scraper.zoopla.shards import SearchFilter, search_path, search_url, split_filter


def test_split_filter_bisects_price() -> None:
    lower, upper = split_filter(SearchFilter(min_price=350_000, max_price=800_000))
    assert lower == SearchFilter(min_price=350_000, max_price=575_000)
    assert upper == SearchFilter(min_price=575_001, max_price=800_000)


def test_split_filter_splits_beds_when_price_is_one_pound() -> None:
    lower, upper = split_filter(SearchFilter(min_price=500_000, max_price=500_000, min_bedrooms=2))
    assert lower.max_bedrooms == 11
    assert upper.min_bedrooms == 12


def test_split_filter_rejects_atomic_filter() -> None:
    with pytest.raises(ValueError, match="cannot split"):
        split_filter(
            SearchFilter(min_price=500_000, max_price=500_000, min_bedrooms=2, max_bedrooms=2)
        )


def test_search_url_uses_houses_path_and_omits_q() -> None:
    url = search_url(
        SearchFilter(
            min_price=350_000,
            max_price=800_000,
            min_bedrooms=2,
            property_types=("detached", "terraced"),
            tenure="FREEHOLD",
        ),
        1,
    )
    assert url.startswith(f"{ZOOPLA_ORIGIN}/for-sale/houses/london/?")
    assert "price_min=350000" in url
    assert "price_max=800000" in url
    assert "beds_min=2" in url
    assert "tenure=freehold" in url
    assert "pn=1" in url
    assert "q=" not in url


def test_search_url_uses_property_path_when_types_omitted() -> None:
    url = search_url(SearchFilter(min_price=350_000, max_price=800_000), 2)
    assert search_path(SearchFilter(min_price=350_000, max_price=800_000)).endswith(
        "/for-sale/property/london/"
    )
    assert "/for-sale/property/london/" in url
    assert "pn=2" in url
    assert "tenure=" not in url
    assert "beds_min=" not in url
