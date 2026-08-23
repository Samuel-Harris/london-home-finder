import json
from pathlib import Path

import pytest
from lhf.listings.listing import NearestStation
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
            property_type="flat",
            property_sub_type="Maisonette",
            key_features="Private garden\nLift",
            description="A maisonette somewhere.",
            bathrooms=9,
            latitude=51.0,
            longitude=-0.12,
            nearest_stations=(
                NearestStation(
                    name="Westminster Station",
                    types=("LONDON_UNDERGROUND", "NATIONAL_TRAIN"),
                    distance=0.15,
                    unit="miles",
                ),
                NearestStation(
                    name="St James's Park Station",
                    types=("LONDON_UNDERGROUND",),
                    distance=0.4,
                    unit="miles",
                ),
                NearestStation(
                    name="Waterloo Station",
                    types=("NATIONAL_TRAIN",),
                    distance=0.9,
                    unit="miles",
                ),
            ),
            listing_update_reason="Reduced on 12/05/2026",
            listing_update_date="2026-05-12T10:00:00Z",
            first_visible_date="2026-01-15T12:00:00Z",
        )
    ]
    state.details = {
        "111111": None,
        "222222": PropertyDetail(
            display_address="10 Downing Street",
            bedrooms=3,
            garden="Private garden",
            parking="Allocated underground",
        ),
    }
    save_checkpoint(path, state)

    loaded = load_checkpoint(path)
    assert loaded == state
    assert loaded.cards[0].bedrooms is None
    assert loaded.cards[0].property_type == "flat"
    assert loaded.cards[0].property_sub_type == "Maisonette"
    assert loaded.cards[0].key_features == "Private garden\nLift"
    assert loaded.cards[0].description == "A maisonette somewhere."
    assert loaded.cards[0].bathrooms == 9
    assert loaded.cards[0].longitude == -0.12
    assert loaded.cards[0].nearest_stations is not None
    assert len(loaded.cards[0].nearest_stations) == 3
    assert loaded.cards[0].nearest_stations[0].types == ("LONDON_UNDERGROUND", "NATIONAL_TRAIN")
    assert loaded.cards[0].listing_update_reason == "Reduced on 12/05/2026"
    assert loaded.details["111111"] is None
    assert loaded.details["222222"] is not None
    assert loaded.details["222222"].display_address == "10 Downing Street"
    assert loaded.details["222222"].garden == "Private garden"
    assert json.loads(path.read_text(encoding="utf-8"))["search_url_base"] == SEARCH_URL


def test_load_treats_missing_screening_fields_as_absent(tmp_path: Path) -> None:
    path = tmp_path / "db.sqlite3.scrape-checkpoint.json"
    state = new_checkpoint(300_000, 1_000_000, None)
    state.cards = [
        SearchCard(listing_id="111111", url="https://www.rightmove.co.uk/properties/111111")
    ]
    state.details = {"111111": PropertyDetail(display_address="10 Downing Street")}
    save_checkpoint(path, state)
    payload = json.loads(path.read_text(encoding="utf-8"))
    for field_name in (
        "property_type",
        "property_sub_type",
        "key_features",
        "description",
        "bathrooms",
        "latitude",
        "longitude",
        "nearest_stations",
        "listing_update_reason",
        "listing_update_date",
        "first_visible_date",
    ):
        del payload["cards"][0][field_name]
    for field_name in (
        "property_type",
        "property_sub_type",
        "key_features",
        "description",
        "bathrooms",
        "garden",
        "parking",
        "latitude",
        "longitude",
        "nearest_stations",
        "listing_update_reason",
        "listing_update_date",
        "first_visible_date",
    ):
        del payload["details"]["111111"][field_name]
    path.write_text(json.dumps(payload), encoding="utf-8")

    loaded = load_checkpoint(path)
    assert loaded.cards[0].property_type is None
    assert loaded.cards[0].nearest_stations is None
    assert loaded.details["111111"] is not None
    assert loaded.details["111111"].garden is None
    assert loaded.details["111111"].display_address == "10 Downing Street"


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
