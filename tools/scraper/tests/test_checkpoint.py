import json
from pathlib import Path

import pytest
from lhf.scraper.checkpoint import (
    CHECKPOINT_VERSION,
    ActiveShard,
    checkpoint_path,
    clear_checkpoint,
    load_checkpoint,
    new_checkpoint,
    save_checkpoint,
)
from lhf.scraper.detail import PropertyDetail
from lhf.scraper.search import SearchCard
from lhf.scraper.shards import SEARCH_URL, SearchFilter


def test_checkpoint_path_appends_suffix(tmp_path: Path) -> None:
    database_path = tmp_path / "london-home-finder.sqlite3"
    assert checkpoint_path(database_path) == Path(f"{database_path}.scrape-checkpoint.json")


def test_round_trip_preserves_null_bedrooms_and_null_detail(tmp_path: Path) -> None:
    path = tmp_path / "db.sqlite3.scrape-checkpoint.json"
    state = new_checkpoint(300_000, 1_000_000, None)
    state.pending_filters = [
        SearchFilter(min_price=300_000, max_price=650_000, min_bedrooms=None, max_bedrooms=None)
    ]
    state.active = ActiveShard(
        filter=SearchFilter(min_price=650_001, max_price=1_000_000, min_bedrooms=2, max_bedrooms=4),
        next_index=24,
    )
    state.cards = [
        SearchCard(
            listing_id="111111",
            url="https://www.rightmove.co.uk/properties/111111",
            bedrooms=None,
        )
    ]
    state.details = {
        "111111": None,
        "222222": PropertyDetail(display_address="10 Downing Street", bedrooms=3),
    }
    save_checkpoint(path, state)

    loaded = load_checkpoint(path)
    assert loaded == state
    assert loaded.cards[0].bedrooms is None
    assert loaded.details["111111"] is None
    assert loaded.details["222222"] is not None
    assert loaded.details["222222"].display_address == "10 Downing Street"
    assert json.loads(path.read_text(encoding="utf-8"))["search_url_base"] == SEARCH_URL


def test_save_replaces_into_final_path_and_leaves_it_readable(tmp_path: Path) -> None:
    path = tmp_path / "db.sqlite3.scrape-checkpoint.json"
    state = new_checkpoint(300_000, 1_000_000, 3)
    save_checkpoint(path, state)

    assert path.is_file()
    assert not path.with_name(path.name + ".tmp").exists()
    text = path.read_text(encoding="utf-8")
    assert text.startswith(f'{{"version":{CHECKPOINT_VERSION},')
    assert load_checkpoint(path).max_pages == 3


def test_clear_removes_json_and_tmp(tmp_path: Path) -> None:
    path = tmp_path / "db.sqlite3.scrape-checkpoint.json"
    tmp = path.with_name(path.name + ".tmp")
    path.write_text("{}", encoding="utf-8")
    tmp.write_text("{}", encoding="utf-8")

    clear_checkpoint(path)

    assert not path.exists()
    assert not tmp.exists()
    clear_checkpoint(path)


def test_load_missing_file_includes_path(tmp_path: Path) -> None:
    path = tmp_path / "missing.scrape-checkpoint.json"
    with pytest.raises(ValueError, match="no scrape checkpoint to resume at") as exc_info:
        load_checkpoint(path)
    assert str(path) in str(exc_info.value)


def test_load_unsupported_version(tmp_path: Path) -> None:
    path = tmp_path / "db.sqlite3.scrape-checkpoint.json"
    path.write_text(json.dumps({"version": 2}), encoding="utf-8")
    with pytest.raises(ValueError, match="scrape checkpoint version 2 is not supported"):
        load_checkpoint(path)


def test_load_invalid_json(tmp_path: Path) -> None:
    path = tmp_path / "db.sqlite3.scrape-checkpoint.json"
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(ValueError, match="scrape checkpoint is invalid"):
        load_checkpoint(path)
