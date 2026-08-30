import json
from pathlib import Path

import pytest
from lhf.db.session import create_session_factory
from lhf.db_app.migrations import upgrade_database
from lhf.listings.listing import ListingDraft
from lhf.listings.listing_repository import ListingRepository
from lhf.scraper.onthemarket.checkpoint import checkpoint_path
from lhf.scraper.onthemarket.http import EmptyPage, FetchError
from lhf.scraper.onthemarket.scrape import scrape
from lhf.scraper.onthemarket.shards import LONDON_LOCAL_AUTHORITIES, ORIGIN, PAGE_RESULT_CAP
from lhf.scraper.window import IngestWindow

FIXTURES = Path(__file__).parent / "fixtures"


def test_detail_303_maps_search_card_and_persists(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database_path = tmp_path / "scrape.sqlite3"
    upgrade_database(database_path)

    def fake_get(_self: object, url: str) -> str:
        if "/details/" in url:
            raise EmptyPage(f"HTTP 303 fetching {url}")
        if "?page=" in url:
            raise EmptyPage(f"HTTP 303 fetching {url}")
        if "/for-sale/2-bed-houses/london/" in url:
            return _search_html(
                1,
                [_card("19924482", "£650,000", "Terraced house", "Freehold", bedrooms=3)],
            )
        return _search_html(0, [])

    monkeypatch.setattr("lhf.scraper.onthemarket.scrape.Fetcher.get", fake_get)

    assert scrape(database_path) == 1
    listings = ListingRepository(create_session_factory(database_path)).list_all()
    assert listings[0].external_id == "19924482"
    assert listings[0].asking_price_gbp == 650_000


def test_empty_crawl_does_not_wipe_existing_rows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database_path = tmp_path / "scrape.sqlite3"
    upgrade_database(database_path)
    repository = ListingRepository(create_session_factory(database_path))
    repository.replace_source(
        "rightmove",
        [
            ListingDraft(
                source="rightmove",
                external_id="kept-rightmove",
                url="https://www.rightmove.co.uk/properties/kept",
            )
        ],
    )
    repository.replace_source(
        "onthemarket",
        [
            ListingDraft(
                source="onthemarket",
                external_id="kept-otm",
                url="https://www.onthemarket.com/details/kept/",
            )
        ],
    )

    def empty(_self: object, url: str) -> str:
        return _search_html(0, [])

    monkeypatch.setattr("lhf.scraper.onthemarket.scrape.Fetcher.get", empty)

    with pytest.raises(ValueError, match="scrape produced no listings"):
        scrape(database_path)

    listings = repository.list_all()
    assert {(listing.source, listing.external_id) for listing in listings} == {
        ("rightmove", "kept-rightmove"),
        ("onthemarket", "kept-otm"),
    }


def test_303_ends_shard_and_persists_in_cap_cards(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database_path = tmp_path / "scrape.sqlite3"
    upgrade_database(database_path)
    fetched: list[str] = []

    def fake_get(_self: object, url: str) -> str:
        fetched.append(url)
        if "/details/" in url:
            if url.endswith("/details/19924482/"):
                return (FIXTURES / "detail-19924482.html").read_text(encoding="utf-8")
            raise FetchError(f"HTTP 500 fetching {url}")
        if "?page=" in url:
            raise EmptyPage(f"HTTP 303 fetching {url}")
        if "/for-sale/2-bed-houses/london/" in url:
            return _search_html(
                1,
                [_card("19924482", "£650,000", "Terraced house", "Freehold", bedrooms=3)],
            )
        return _search_html(0, [])

    monkeypatch.setattr("lhf.scraper.onthemarket.scrape.Fetcher.get", fake_get)

    assert scrape(database_path) == 1
    listings = ListingRepository(create_session_factory(database_path)).list_all()
    assert [listing.external_id for listing in listings] == ["19924482"]
    assert listings[0].source == "onthemarket"
    assert any("?page=2" in url for url in fetched)
    assert not checkpoint_path(database_path).exists()


def test_replace_source_leaves_rightmove_rows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database_path = tmp_path / "scrape.sqlite3"
    upgrade_database(database_path)
    repository = ListingRepository(create_session_factory(database_path))
    repository.replace_source(
        "rightmove",
        [
            ListingDraft(
                source="rightmove",
                external_id="kept-rightmove",
                url="https://www.rightmove.co.uk/properties/kept",
            )
        ],
    )

    def fake_get(_self: object, url: str) -> str:
        if "/details/19924482/" in url:
            return (FIXTURES / "detail-19924482.html").read_text(encoding="utf-8")
        if "/details/" in url:
            raise FetchError(f"HTTP 500 fetching {url}")
        if "?page=" in url:
            raise EmptyPage(f"HTTP 303 fetching {url}")
        if "/for-sale/2-bed-houses/london/" in url:
            return _search_html(
                1,
                [_card("19924482", "£650,000", "Terraced house", "Freehold", bedrooms=3)],
            )
        return _search_html(0, [])

    monkeypatch.setattr("lhf.scraper.onthemarket.scrape.Fetcher.get", fake_get)

    assert scrape(database_path) == 1
    listings = repository.list_all()
    assert {(listing.source, listing.external_id) for listing in listings} == {
        ("rightmove", "kept-rightmove"),
        ("onthemarket", "19924482"),
    }


def test_overflow_does_not_keep_parent_cards(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database_path = tmp_path / "scrape.sqlite3"
    upgrade_database(database_path)
    fetched: list[str] = []

    def fake_get(_self: object, url: str) -> str:
        fetched.append(url)
        if "/details/" in url:
            raise FetchError(f"HTTP 500 fetching {url}")
        if "/for-sale/2-bed-houses/london/" in url:
            return _search_html(
                PAGE_RESULT_CAP + 1,
                [_card("999999", "£400,000", "Terraced house", "Freehold", bedrooms=2)],
            )
        if "/for-sale/2-bed-terraced/islington/" in url:
            return _search_html(
                1,
                [_card("19924482", "£650,000", "Terraced house", "Freehold", bedrooms=3)],
            )
        if "/for-sale/2-bed-" in url and "/london/" in url:
            return _search_html(PAGE_RESULT_CAP + 1, [_card("888888", "£400,000", "House")])
        return _search_html(0, [])

    monkeypatch.setattr("lhf.scraper.onthemarket.scrape.Fetcher.get", fake_get)

    count = scrape(database_path, max_pages=1)
    listings = ListingRepository(create_session_factory(database_path)).list_all()
    ids = {listing.external_id for listing in listings}
    assert "999999" not in ids
    assert "888888" not in ids
    assert count == 1
    assert "19924482" in ids
    overflow_url = f"{ORIGIN}/for-sale/2-bed-houses/london/"
    assert overflow_url in fetched
    assert f"{ORIGIN}/for-sale/2-bed-terraced/islington/" in fetched
    assert not any("min-price" in url for url in fetched)
    assert len(LONDON_LOCAL_AUTHORITIES) == 33


def test_unsplittable_overflow_does_not_wipe(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database_path = tmp_path / "scrape.sqlite3"
    upgrade_database(database_path)
    repository = ListingRepository(create_session_factory(database_path))
    repository.replace_source(
        "onthemarket",
        [
            ListingDraft(
                source="onthemarket",
                external_id="kept-otm",
                url="https://www.onthemarket.com/details/kept/",
            )
        ],
    )

    def fake_get(_self: object, url: str) -> str:
        return _search_html(PAGE_RESULT_CAP + 1, [_card("1", "£500,000", "Terraced house")])

    monkeypatch.setattr("lhf.scraper.onthemarket.scrape.Fetcher.get", fake_get)

    with pytest.raises(FetchError, match="unsplittable shard"):
        scrape(
            database_path,
            window=IngestWindow(property_types=("terraced",), tenure=None),
        )

    assert [listing.external_id for listing in repository.list_all()] == ["kept-otm"]


def test_scrape_rejects_invalid_max_pages_before_fetch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail(_self: object, url: str) -> str:
        raise FetchError(f"should not fetch {url}")

    monkeypatch.setattr("lhf.scraper.onthemarket.scrape.Fetcher.get", fail)

    with pytest.raises(ValueError, match="max_pages"):
        scrape(tmp_path / "scrape.sqlite3", max_pages=0)


def _search_html(total_results: int, properties: list[dict[str, object]]) -> str:
    payload = {
        "props": {
            "initialReduxState": {"results": {"totalResults": total_results, "list": properties}}
        }
    }
    return (
        '<script id="__NEXT_DATA__" type="application/json">'
        + json.dumps(payload, separators=(",", ":"))
        + "</script>"
    )


def _card(
    listing_id: str,
    price: str,
    property_type: str,
    tenure: str | None = "Freehold",
    *,
    bedrooms: int = 3,
) -> dict[str, object]:
    features = [f"Tenure: {tenure}"] if tenure is not None else []
    return {
        "id": listing_id,
        "details-url": f"/details/{listing_id}/",
        "address": f"{listing_id} Street",
        "price": price,
        "bedrooms": bedrooms,
        "humanised-property-type": property_type,
        "features": features,
    }
