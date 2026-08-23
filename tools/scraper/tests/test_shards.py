import pytest
from lhf.scraper.shards import SEARCH_URL, SearchFilter, search_url, split_filter


def test_split_filter_bisects_price() -> None:
    lower, upper = split_filter(SearchFilter(min_price=300_000, max_price=1_000_000))

    assert lower == SearchFilter(min_price=300_000, max_price=650_000)
    assert upper == SearchFilter(min_price=650_001, max_price=1_000_000)


def test_split_filter_keeps_bed_bounds_when_splitting_price() -> None:
    lower, upper = split_filter(
        SearchFilter(min_price=300_000, max_price=1_000_000, min_bedrooms=2, max_bedrooms=4)
    )

    assert lower.min_bedrooms == 2 and lower.max_bedrooms == 4
    assert upper.min_bedrooms == 2 and upper.max_bedrooms == 4


def test_split_filter_splits_beds_when_price_is_one_pound() -> None:
    lower, upper = split_filter(SearchFilter(min_price=500_000, max_price=500_000))

    assert lower == SearchFilter(
        min_price=500_000, max_price=500_000, min_bedrooms=0, max_bedrooms=10
    )
    assert upper == SearchFilter(
        min_price=500_000, max_price=500_000, min_bedrooms=11, max_bedrooms=20
    )


def test_split_filter_bisects_existing_bedroom_range() -> None:
    lower, upper = split_filter(
        SearchFilter(min_price=500_000, max_price=500_000, min_bedrooms=0, max_bedrooms=10)
    )

    assert lower == SearchFilter(
        min_price=500_000, max_price=500_000, min_bedrooms=0, max_bedrooms=5
    )
    assert upper == SearchFilter(
        min_price=500_000, max_price=500_000, min_bedrooms=6, max_bedrooms=10
    )


def test_split_filter_rejects_atomic_filter() -> None:
    with pytest.raises(ValueError, match="cannot split"):
        split_filter(
            SearchFilter(min_price=500_000, max_price=500_000, min_bedrooms=2, max_bedrooms=2)
        )


def test_search_url_omits_index_and_beds_on_first_page() -> None:
    url = search_url(SearchFilter(min_price=300_000, max_price=1_000_000), 0)

    assert url.startswith(SEARCH_URL)
    assert "minPrice=300000" in url
    assert "maxPrice=1000000" in url
    assert "index=" not in url
    assert "Bedrooms" not in url


def test_search_url_includes_index_and_bed_bounds() -> None:
    url = search_url(
        SearchFilter(min_price=500_000, max_price=500_000, min_bedrooms=0, max_bedrooms=10),
        24,
    )

    assert "minPrice=500000" in url
    assert "maxPrice=500000" in url
    assert "minBedrooms=0" in url
    assert "maxBedrooms=10" in url
    assert "index=24" in url
