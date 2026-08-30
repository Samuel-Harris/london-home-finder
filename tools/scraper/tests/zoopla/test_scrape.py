from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest
from lhf.db.session import create_session_factory
from lhf.db_app.migrations import upgrade_database
from lhf.listings.listing import ListingDraft
from lhf.listings.listing_repository import ListingRepository
from lhf.scraper.window import IngestWindow
from lhf.scraper.zoopla.checkpoint import checkpoint_path
from lhf.scraper.zoopla.http import FetchError
from lhf.scraper.zoopla.scrape import scrape

FIXTURES = Path(__file__).parent / "fixtures"
UNUSABLE_SEARCH = "<html>couldn't find properties</html>"


def _flight_html(flight: str) -> str:
    inner = json.dumps(flight)[1:-1]
    return f'<script>self.__next_f.push([1,"{inner}"])</script>'


def _search_html(
    listing_id: str,
    price: int,
    *,
    result_count: int = 1,
    page_number: int = 1,
    page_number_max: int = 1,
) -> str:
    card = {
        "listingId": listing_id,
        "listingUris": {"detail": f"/for-sale/details/{listing_id}/"},
        "address": "Example Road",
        "priceUnformatted": price,
        "priceTitle": None,
        "propertyType": "terraced",
        "sizeSqft": 800,
        "pos": {"lat": 51.5, "lng": -0.1},
        "features": [{"content": 2, "iconId": "bed"}, {"content": 1, "iconId": "bath"}],
        "tags": [{"content": "Freehold"}],
        "summaryDescription": "A house.",
        "flag": None,
        "publishedOn": "30th Aug 2026",
    }
    flight = (
        '"regularListingsFormatted":'
        + json.dumps([card])
        + ',"pagination":'
        + json.dumps(
            {
                "pageNumber": page_number,
                "pageNumberMax": page_number_max,
                "totalResults": result_count,
            }
        )
    )
    return _flight_html(flight)


def _empty_search_html() -> str:
    return _flight_html(
        '"regularListingsFormatted":[],"pagination":'
        '{"pageNumber":1,"pageNumberMax":1,"totalResults":0}'
    )


def _recorded_get(search_html: str, details: dict[str, str]):
    def get(_self: object, url: str) -> str:
        if "/for-sale/details/" in url:
            listing_id = url.rstrip("/").rsplit("/", 1)[-1]
            return details[listing_id]
        return search_html

    return get


def _seed_both_sources(database_path: Path) -> ListingRepository:
    repository = ListingRepository(create_session_factory(database_path))
    repository.replace_all(
        [
            ListingDraft(
                source="rightmove",
                external_id="kept-rm",
                url="https://www.rightmove.co.uk/properties/kept",
            )
        ]
    )
    repository.replace_zoopla(
        [
            ListingDraft(
                source="zoopla",
                external_id="kept-z",
                url="https://www.zoopla.co.uk/for-sale/details/kept/",
            )
        ]
    )
    return repository


def test_scrape_maps_recorded_pages_into_zoopla_table(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database_path = tmp_path / "scrape.sqlite3"
    upgrade_database(database_path)
    search_html = _search_html("74103170", 450000)
    detail_html = (FIXTURES / "detail.html").read_text(encoding="utf-8")
    monkeypatch.setattr(
        "lhf.scraper.zoopla.scrape.Fetcher.get",
        _recorded_get(search_html, {"74103170": detail_html}),
    )

    assert scrape(database_path) == 1
    listings = ListingRepository(create_session_factory(database_path)).list_all()
    assert [listing.external_id for listing in listings] == ["74103170"]
    assert listings[0].source == "zoopla"
    assert listings[0].postcode == "SM5 1PN"
    assert not checkpoint_path(database_path).exists()


def test_failed_search_does_not_wipe_existing_zoopla_or_rightmove_rows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database_path = tmp_path / "scrape.sqlite3"
    upgrade_database(database_path)
    repository = _seed_both_sources(database_path)

    def fail(_self: object, url: str) -> str:
        raise FetchError(f"timeout fetching {url}")

    monkeypatch.setattr("lhf.scraper.zoopla.scrape.Fetcher.get", fail)

    with pytest.raises(FetchError, match="timeout"):
        scrape(database_path)

    assert [(listing.source, listing.external_id) for listing in repository.list_all()] == [
        ("rightmove", "kept-rm"),
        ("zoopla", "kept-z"),
    ]


def test_unusable_search_html_does_not_wipe_existing_rows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database_path = tmp_path / "scrape.sqlite3"
    upgrade_database(database_path)
    repository = _seed_both_sources(database_path)

    def unusable(_self: object, url: str) -> str:
        return UNUSABLE_SEARCH

    monkeypatch.setattr("lhf.scraper.zoopla.scrape.Fetcher.get", unusable)

    with pytest.raises(FetchError, match="missing __next_f"):
        scrape(database_path)

    assert [(listing.source, listing.external_id) for listing in repository.list_all()] == [
        ("rightmove", "kept-rm"),
        ("zoopla", "kept-z"),
    ]
    assert checkpoint_path(database_path).is_file()


def test_empty_search_results_do_not_wipe_existing_rows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database_path = tmp_path / "scrape.sqlite3"
    upgrade_database(database_path)
    repository = _seed_both_sources(database_path)

    def empty(_self: object, url: str) -> str:
        return _empty_search_html()

    monkeypatch.setattr("lhf.scraper.zoopla.scrape.Fetcher.get", empty)

    with pytest.raises(ValueError, match="scrape produced no listings"):
        scrape(database_path)

    assert [(listing.source, listing.external_id) for listing in repository.list_all()] == [
        ("rightmove", "kept-rm"),
        ("zoopla", "kept-z"),
    ]


def test_overflowing_unsplittable_shard_does_not_persist(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database_path = tmp_path / "scrape.sqlite3"
    upgrade_database(database_path)
    repository = _seed_both_sources(database_path)
    search_html = _search_html("1", 500000, result_count=1001)

    def get(_self: object, url: str) -> str:
        return search_html

    monkeypatch.setattr("lhf.scraper.zoopla.scrape.Fetcher.get", get)

    with pytest.raises(FetchError, match="still exceeds"):
        scrape(
            database_path,
            window=IngestWindow(
                min_price=500_000,
                max_price=500_000,
                min_bedrooms=2,
                property_types=("detached",),
                tenure="FREEHOLD",
            ),
        )

    assert [(listing.source, listing.external_id) for listing in repository.list_all()] == [
        ("rightmove", "kept-rm"),
        ("zoopla", "kept-z"),
    ]
    assert checkpoint_path(database_path).is_file()


def test_later_page_http_404_ends_the_shard(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database_path = tmp_path / "scrape.sqlite3"
    upgrade_database(database_path)
    fetched: list[str] = []

    def get(_self: object, url: str) -> str:
        fetched.append(url)
        if "/for-sale/details/" in url:
            raise FetchError(f"HTTP 500 fetching {url}", status=500)
        page_number = parse_qs(urlparse(url).query).get("pn", ["1"])[0]
        if page_number != "1":
            raise FetchError(f"HTTP 404 fetching {url}", status=404)
        return _search_html("1", 400000, result_count=26, page_number=1, page_number_max=40)

    monkeypatch.setattr("lhf.scraper.zoopla.scrape.Fetcher.get", get)

    assert scrape(database_path) == 1
    listings = ListingRepository(create_session_factory(database_path)).list_all()
    assert [listing.external_id for listing in listings] == ["1"]
    search_pages = [
        parse_qs(urlparse(url).query).get("pn", ["1"])[0]
        for url in fetched
        if "/for-sale/details/" not in url
    ]
    assert search_pages == ["1", "2"]
