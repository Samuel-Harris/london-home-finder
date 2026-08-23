import json
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest
from lhf.db.session import create_session_factory
from lhf.db_app.migrations import upgrade_database
from lhf.listings.listing import ListingDraft
from lhf.listings.listing_repository import ListingRepository
from lhf.scraper.checkpoint import (
    ActiveShard,
    checkpoint_path,
    load_checkpoint,
    new_checkpoint,
    save_checkpoint,
)
from lhf.scraper.http import FetchError
from lhf.scraper.scrape import scrape
from lhf.scraper.shards import SearchFilter

FIXTURES = Path(__file__).parent / "fixtures"
EMPTY_SEARCH = "<html>couldn't find properties</html>"


def test_scrape_maps_recorded_pages_and_deduplicates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database_path = tmp_path / "scrape.sqlite3"
    upgrade_database(database_path)
    monkeypatch.setattr("lhf.scraper.scrape.Fetcher.get", _recorded_get)

    assert scrape(database_path) == 2
    listings = ListingRepository(create_session_factory(database_path)).list_all()
    assert [listing.external_id for listing in listings] == ["111111", "222222"]
    assert listings[0].asking_price_gbp is None
    assert listings[0].property_type == "flat"
    assert listings[0].property_sub_type == "Maisonette"
    assert listings[0].annual_service_charge_gbp == 2400
    assert listings[0].key_features == "Private garden\nLift"
    assert listings[0].description == "A leasehold maisonette.<br /><br />Private garden."
    assert listings[0].bathrooms == 1
    assert listings[0].garden == "Yes"
    assert listings[0].parking == "Allocated underground"
    assert listings[0].longitude == -0.1416
    assert listings[0].nearest_stations is not None
    assert [station.name for station in listings[0].nearest_stations] == [
        "Westminster Station",
        "Waterloo Station",
    ]
    assert listings[1].years_remaining_on_lease is None
    assert listings[1].postcode == "SW1A 2AA"
    assert listings[1].property_type == "house"
    assert listings[1].property_sub_type == "Terraced"
    assert listings[1].key_features == "Rear garden\nPeriod features"
    assert listings[1].description == "A terraced house in Westminster."


def test_failed_search_does_not_wipe_existing_rows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database_path = tmp_path / "scrape.sqlite3"
    upgrade_database(database_path)
    repository = ListingRepository(create_session_factory(database_path))
    repository.replace_all(
        [
            ListingDraft(
                source="rightmove",
                external_id="kept",
                url="https://www.rightmove.co.uk/properties/kept",
            )
        ]
    )

    def fail(_self: object, url: str) -> str:
        raise FetchError(f"timeout fetching {url}")

    monkeypatch.setattr("lhf.scraper.scrape.Fetcher.get", fail)

    with pytest.raises(FetchError, match="timeout"):
        scrape(database_path)

    assert [listing.external_id for listing in repository.list_all()] == ["kept"]


def test_detail_failure_keeps_the_search_card(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    database_path = tmp_path / "scrape.sqlite3"
    upgrade_database(database_path)

    def fake_get(_self: object, url: str) -> str:
        if "find.html" in url:
            if "index=" in url:
                return EMPTY_SEARCH
            return (FIXTURES / "search.html").read_text(encoding="utf-8")
        raise FetchError(f"HTTP 500 fetching {url}")

    monkeypatch.setattr("lhf.scraper.scrape.Fetcher.get", fake_get)

    assert scrape(database_path) == 2
    listings = ListingRepository(create_session_factory(database_path)).list_all()
    assert [listing.external_id for listing in listings] == ["111111", "222222"]
    assert listings[0].annual_service_charge_gbp is None
    assert listings[1].postcode is None
    assert "warning: failed to fetch detail" in capsys.readouterr().err


def test_scrape_splits_overflow_and_unions_in_band_ids(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    database_path = tmp_path / "scrape.sqlite3"
    upgrade_database(database_path)
    fetched: list[str] = []

    def fake_get(_self: object, url: str) -> str:
        fetched.append(url)
        if url.endswith("/properties/111111"):
            return (FIXTURES / "detail_leasehold.html").read_text(encoding="utf-8")
        if url.endswith("/properties/222222"):
            return (FIXTURES / "detail_freehold.html").read_text(encoding="utf-8")
        if "/properties/" in url:
            raise FetchError(f"HTTP 500 fetching {url}")
        params = _query(url)
        if "index" in params:
            return EMPTY_SEARCH
        min_price, max_price = params["minPrice"], params["maxPrice"]
        if min_price == "300000" and max_price == "1000000":
            return _search_html(2000, [_property(999999, 400_000)])
        if min_price == "300000" and max_price == "650000":
            return _search_html(
                3,
                [
                    _property(111111, None),
                    _property(222222, 650_000),
                    _property(333333, 2_000_000),
                ],
            )
        if min_price == "650001" and max_price == "1000000":
            return _search_html(
                2,
                [
                    _property(111111, None),
                    _property(444444, 800_000),
                ],
            )
        raise FetchError(f"unexpected url {url}")

    monkeypatch.setattr("lhf.scraper.scrape.Fetcher.get", fake_get)

    assert scrape(database_path) == 3
    listings = ListingRepository(create_session_factory(database_path)).list_all()
    assert [listing.external_id for listing in listings] == ["111111", "222222", "444444"]
    search_urls = [url for url in fetched if "find.html" in url]
    assert any(_query(url)["maxPrice"] == "650000" for url in search_urls)
    assert any(_query(url)["minPrice"] == "650001" for url in search_urls)
    assert "999999" not in {listing.external_id for listing in listings}
    stderr = capsys.readouterr().err
    assert "minPrice=300000 maxPrice=650000 resultCount=3" in stderr
    assert "minPrice=650001 maxPrice=1000000 resultCount=2" in stderr


def test_atomic_overflow_does_not_wipe_existing_rows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database_path = tmp_path / "scrape.sqlite3"
    upgrade_database(database_path)
    repository = ListingRepository(create_session_factory(database_path))
    repository.replace_all(
        [
            ListingDraft(
                source="rightmove",
                external_id="kept",
                url="https://www.rightmove.co.uk/properties/kept",
            )
        ]
    )

    def fake_get(_self: object, url: str) -> str:
        if "find.html" not in url:
            raise FetchError(f"unexpected url {url}")
        return _search_html(2000, [_property(1, 500_000)])

    monkeypatch.setattr("lhf.scraper.scrape.Fetcher.get", fake_get)

    with pytest.raises(FetchError, match="unsplittable filter"):
        scrape(database_path, min_price=500_000, max_price=500_000)

    assert [listing.external_id for listing in repository.list_all()] == ["kept"]


def test_max_pages_stops_after_one_in_cap_search_page(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database_path = tmp_path / "scrape.sqlite3"
    upgrade_database(database_path)
    fetched: list[str] = []

    def fake_get(_self: object, url: str) -> str:
        fetched.append(url)
        if "/properties/" in url:
            raise FetchError(f"HTTP 500 fetching {url}")
        params = _query(url)
        if "index" in params:
            return _search_html(2, [_property(555555, 400_000)])
        min_price, max_price = params["minPrice"], params["maxPrice"]
        if min_price == "300000" and max_price == "1000000":
            return _search_html(2000, [_property(999999, 400_000)])
        if min_price == "300000" and max_price == "650000":
            return (FIXTURES / "search.html").read_text(encoding="utf-8")
        if min_price == "650001" and max_price == "1000000":
            return _search_html(2, [_property(444444, 800_000)])
        raise FetchError(f"unexpected url {url}")

    monkeypatch.setattr("lhf.scraper.scrape.Fetcher.get", fake_get)

    assert scrape(database_path, max_pages=1) == 2
    listings = ListingRepository(create_session_factory(database_path)).list_all()
    assert [listing.external_id for listing in listings] == ["111111", "222222"]
    search_urls = [url for url in fetched if "find.html" in url]
    assert not any("index=" in url for url in search_urls)
    assert not any(_query(url).get("minPrice") == "650001" for url in search_urls)


def test_unlimited_pages_paginates_until_empty(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database_path = tmp_path / "scrape.sqlite3"
    upgrade_database(database_path)
    fetched: list[str] = []

    def fake_get(_self: object, url: str) -> str:
        fetched.append(url)
        if "/properties/" in url:
            raise FetchError(f"HTTP 500 fetching {url}")
        params = _query(url)
        if params.get("index") == "24":
            return _search_html(3, [_property(444444, 800_000)])
        if "index" in params:
            return EMPTY_SEARCH
        return (FIXTURES / "search.html").read_text(encoding="utf-8")

    monkeypatch.setattr("lhf.scraper.scrape.Fetcher.get", fake_get)

    assert scrape(database_path) == 3
    listings = ListingRepository(create_session_factory(database_path)).list_all()
    assert [listing.external_id for listing in listings] == ["111111", "222222", "444444"]
    assert any(_query(url).get("index") == "24" for url in fetched if "find.html" in url)


def test_scrape_rejects_invalid_window_before_fetch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail(_self: object, url: str) -> str:
        raise FetchError(f"should not fetch {url}")

    monkeypatch.setattr("lhf.scraper.scrape.Fetcher.get", fail)

    with pytest.raises(ValueError, match="min_price"):
        scrape(tmp_path / "scrape.sqlite3", min_price=0)
    with pytest.raises(ValueError, match="max_price"):
        scrape(tmp_path / "scrape.sqlite3", min_price=500_000, max_price=400_000)
    with pytest.raises(ValueError, match="max_pages"):
        scrape(tmp_path / "scrape.sqlite3", max_pages=0)


def test_resume_continues_search_from_failed_index(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    database_path = tmp_path / "scrape.sqlite3"
    upgrade_database(database_path)
    repository = ListingRepository(create_session_factory(database_path))
    repository.replace_all(
        [
            ListingDraft(
                source="rightmove",
                external_id="kept",
                url="https://www.rightmove.co.uk/properties/kept",
            )
        ]
    )
    fetched: list[str] = []
    fail_at_48 = True

    def fake_get(_self: object, url: str) -> str:
        fetched.append(url)
        if "/properties/" in url:
            raise FetchError(f"HTTP 500 fetching {url}")
        params = _query(url)
        if params.get("index") == "48":
            if fail_at_48:
                raise FetchError(f"net::ERR_INTERNET_DISCONNECTED fetching {url}")
            return EMPTY_SEARCH
        if params.get("index") == "24":
            return _search_html(3, [_property(444444, 800_000)])
        if "index" in params:
            return EMPTY_SEARCH
        return (FIXTURES / "search.html").read_text(encoding="utf-8")

    monkeypatch.setattr("lhf.scraper.scrape.Fetcher.get", fake_get)

    with pytest.raises(FetchError, match="ERR_INTERNET_DISCONNECTED"):
        scrape(database_path)

    assert [listing.external_id for listing in repository.list_all()] == ["kept"]
    state = load_checkpoint(checkpoint_path(database_path))
    assert state.pages_used == 2
    assert state.active is not None
    assert state.active.next_index == 48
    assert [card.listing_id for card in state.cards] == ["111111", "222222", "444444"]

    fail_at_48 = False
    fetched.clear()
    assert scrape(database_path, resume=True) == 3
    assert [listing.external_id for listing in repository.list_all()] == [
        "111111",
        "222222",
        "444444",
    ]
    assert not checkpoint_path(database_path).exists()
    assert any(_query(url).get("index") == "48" for url in fetched if "find.html" in url)
    stderr = capsys.readouterr().err
    assert (
        "resuming scrape phase=search pages_used=2 cards=3 pending=0"
        " active=minPrice=300000 maxPrice=1000000 next_index=48"
    ) in stderr


def test_resume_skips_saved_detail(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    database_path = tmp_path / "scrape.sqlite3"
    upgrade_database(database_path)
    fetched_details: list[str] = []
    interrupt = True

    def fake_get(_self: object, url: str) -> str:
        if "find.html" in url:
            if "index=" in url:
                return EMPTY_SEARCH
            return (FIXTURES / "search.html").read_text(encoding="utf-8")
        fetched_details.append(url)
        if interrupt and url.endswith("/properties/222222"):
            raise RuntimeError("killed after first detail")
        if url.endswith("/properties/111111"):
            return (FIXTURES / "detail_leasehold.html").read_text(encoding="utf-8")
        if url.endswith("/properties/222222"):
            return (FIXTURES / "detail_freehold.html").read_text(encoding="utf-8")
        raise FetchError(f"unexpected url {url}")

    monkeypatch.setattr("lhf.scraper.scrape.Fetcher.get", fake_get)

    with pytest.raises(RuntimeError, match="killed after first detail"):
        scrape(database_path)

    state = load_checkpoint(checkpoint_path(database_path))
    assert state.phase == "details"
    assert state.details["111111"] is not None
    assert "222222" not in state.details

    fetched_details.clear()
    interrupt = False
    assert scrape(database_path, resume=True) == 2
    assert not any(url.endswith("/properties/111111") for url in fetched_details)
    assert any(url.endswith("/properties/222222") for url in fetched_details)
    assert not checkpoint_path(database_path).exists()
    listings = ListingRepository(create_session_factory(database_path)).list_all()
    assert listings[0].annual_service_charge_gbp == 2400
    assert listings[1].postcode == "SW1A 2AA"


def test_resume_without_checkpoint_does_not_fetch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail(_self: object, url: str) -> str:
        raise FetchError(f"should not fetch {url}")

    monkeypatch.setattr("lhf.scraper.scrape.Fetcher.get", fail)

    with pytest.raises(ValueError, match="no scrape checkpoint"):
        scrape(tmp_path / "scrape.sqlite3", resume=True)


def test_resume_window_mismatch_does_not_fetch_and_keeps_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database_path = tmp_path / "scrape.sqlite3"
    path = checkpoint_path(database_path)
    save_checkpoint(path, new_checkpoint(400_000, 1_000_000, None))

    def fail(_self: object, url: str) -> str:
        raise FetchError(f"should not fetch {url}")

    monkeypatch.setattr("lhf.scraper.scrape.Fetcher.get", fail)

    with pytest.raises(
        ValueError,
        match="scrape checkpoint does not match min_price=300000 max_price=1000000 max_pages=None",
    ):
        scrape(database_path, resume=True)
    assert path.is_file()


def test_fresh_scrape_discards_leftover_checkpoint_and_fetches_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    database_path = tmp_path / "scrape.sqlite3"
    upgrade_database(database_path)
    leftover = new_checkpoint(300_000, 1_000_000, None)
    leftover.active = ActiveShard(
        filter=SearchFilter(min_price=500_000, max_price=500_000, min_bedrooms=2, max_bedrooms=4),
        next_index=48,
    )
    leftover.pending_filters = [
        SearchFilter(min_price=500_000, max_price=500_000, min_bedrooms=5, max_bedrooms=20)
    ]
    path = checkpoint_path(database_path)
    save_checkpoint(path, leftover)
    fetched: list[str] = []

    def fake_get(_self: object, url: str) -> str:
        fetched.append(url)
        return _recorded_get(_self, url)

    monkeypatch.setattr("lhf.scraper.scrape.Fetcher.get", fake_get)

    assert scrape(database_path) == 2
    stderr = capsys.readouterr().err
    assert f"warning: discarding incomplete scrape checkpoint at {path}" in stderr
    first_search = next(url for url in fetched if "find.html" in url)
    params = _query(first_search)
    assert params["minPrice"] == "300000"
    assert params["maxPrice"] == "1000000"
    assert "minBedrooms" not in params
    assert "maxBedrooms" not in params
    assert not any(_query(url).get("minBedrooms") == "2" for url in fetched if "find.html" in url)


def _recorded_get(_self: object, url: str) -> str:
    if "find.html" in url:
        if "index=" in url:
            return EMPTY_SEARCH
        return (FIXTURES / "search.html").read_text(encoding="utf-8")
    if url.endswith("/properties/111111"):
        return (FIXTURES / "detail_leasehold.html").read_text(encoding="utf-8")
    if url.endswith("/properties/222222"):
        return (FIXTURES / "detail_freehold.html").read_text(encoding="utf-8")
    raise FetchError(f"unexpected url {url}")


def _query(url: str) -> dict[str, str]:
    return {key: values[0] for key, values in parse_qs(urlparse(url).query).items()}


def _search_html(result_count: int, properties: list[dict[str, object]]) -> str:
    payload = {
        "props": {
            "pageProps": {"searchResults": {"resultCount": result_count, "properties": properties}}
        }
    }
    return (
        '<script id="__NEXT_DATA__" type="application/json">'
        + json.dumps(payload, separators=(",", ":"))
        + "</script>"
    )


def _property(listing_id: int, amount: int | None) -> dict[str, object]:
    return {
        "id": listing_id,
        "displayAddress": f"{listing_id} Street",
        "price": {"amount": 0 if amount is None else amount},
        "propertyUrl": f"/properties/{listing_id}",
    }
