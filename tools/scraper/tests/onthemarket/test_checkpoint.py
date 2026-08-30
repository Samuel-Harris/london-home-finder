import json
from pathlib import Path

import pytest
from lhf.listings.listing import NearestStation
from lhf.scraper.onthemarket.checkpoint import (
    CHECKPOINT_VERSION,
    ActiveShard,
    checkpoint_path,
    clear_checkpoint,
    load_checkpoint,
    new_checkpoint,
    save_checkpoint,
)
from lhf.scraper.onthemarket.detail import PropertyDetail
from lhf.scraper.onthemarket.search import SearchCard
from lhf.scraper.onthemarket.shards import UNBOUNDED_MAX_BEDROOMS, ShardFilter, houses_spine
from lhf.scraper.window import DEFAULT_WINDOW, IngestWindow


def test_checkpoint_path_uses_onthemarket_suffix(tmp_path: Path) -> None:
    database_path = tmp_path / "london-home-finder.sqlite3"
    assert checkpoint_path(database_path) == Path(
        f"{database_path}.onthemarket-scrape-checkpoint.json"
    )


def test_round_trip_preserves_null_detail_and_window(tmp_path: Path) -> None:
    path = tmp_path / "db.sqlite3.onthemarket-scrape-checkpoint.json"
    state = new_checkpoint(DEFAULT_WINDOW, None)
    state.pending = [ShardFilter(bedrooms=2, property_kind="terraced", location="islington")]
    state.active = ActiveShard(
        filter=ShardFilter(bedrooms=2, property_kind="houses", location="london"),
        next_page=2,
    )
    state.cards = [
        SearchCard(
            listing_id="19924482",
            url="https://www.onthemarket.com/details/19924482/",
            bedrooms=3,
            property_type="Terraced house",
            tenure_type="Freehold",
        )
    ]
    state.details = {
        "19924482": None,
        "20226126": PropertyDetail(
            listing_id="20226126",
            url="https://www.onthemarket.com/details/20226126/",
            tenure_type=None,
            nearest_stations=(
                NearestStation(name="Phipps Bridge Tram Stop", types=("default-network",)),
            ),
        ),
    }
    save_checkpoint(path, state)

    loaded = load_checkpoint(path)
    assert loaded == state
    assert loaded.window == DEFAULT_WINDOW
    assert loaded.cards[0].bedrooms == 3
    assert loaded.details["19924482"] is None
    assert loaded.details["20226126"] is not None
    assert loaded.details["20226126"].tenure_type is None
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["version"] == CHECKPOINT_VERSION
    assert payload["pending"][0]["property_kind"] == "terraced"


def test_new_checkpoint_starts_houses_spine_at_min_bedrooms() -> None:
    state = new_checkpoint(IngestWindow(min_bedrooms=3), 4)
    assert state.pending == list(houses_spine(3))
    assert state.pending[0] == ShardFilter(bedrooms=3, property_kind="houses", location="london")
    assert state.pending[-1].bedrooms == UNBOUNDED_MAX_BEDROOMS
    assert state.max_pages == 4
    assert state.phase == "search"


def test_new_checkpoint_rejects_unknown_property_type() -> None:
    with pytest.raises(ValueError, match="unknown property type"):
        new_checkpoint(IngestWindow(property_types=("flat",), tenure=None), None)


def test_save_replaces_into_final_path_and_leaves_it_readable(tmp_path: Path) -> None:
    path = tmp_path / "db.sqlite3.onthemarket-scrape-checkpoint.json"
    state = new_checkpoint(DEFAULT_WINDOW, 3)
    save_checkpoint(path, state)

    assert path.is_file()
    assert not path.with_name(path.name + ".tmp").exists()
    assert load_checkpoint(path).max_pages == 3


def test_clear_removes_json_and_tmp(tmp_path: Path) -> None:
    path = tmp_path / "db.sqlite3.onthemarket-scrape-checkpoint.json"
    tmp = path.with_name(path.name + ".tmp")
    path.write_text("{}", encoding="utf-8")
    tmp.write_text("{}", encoding="utf-8")

    clear_checkpoint(path)

    assert not path.exists()
    assert not tmp.exists()
    clear_checkpoint(path)


def test_load_missing_file_includes_path(tmp_path: Path) -> None:
    path = tmp_path / "missing.onthemarket-scrape-checkpoint.json"
    with pytest.raises(
        ValueError, match="no onthemarket scrape checkpoint to resume at"
    ) as exc_info:
        load_checkpoint(path)
    assert str(path) in str(exc_info.value)


def test_load_unsupported_version(tmp_path: Path) -> None:
    path = tmp_path / "db.sqlite3.onthemarket-scrape-checkpoint.json"
    path.write_text(json.dumps({"version": 2}), encoding="utf-8")
    with pytest.raises(
        ValueError, match="onthemarket scrape checkpoint version 2 is not supported"
    ):
        load_checkpoint(path)


def test_load_invalid_json(tmp_path: Path) -> None:
    path = tmp_path / "db.sqlite3.onthemarket-scrape-checkpoint.json"
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(ValueError, match="onthemarket scrape checkpoint is invalid"):
        load_checkpoint(path)
