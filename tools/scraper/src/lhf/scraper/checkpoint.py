from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal, cast

from lhf.listings.listing import NearestStation
from lhf.scraper.detail import PropertyDetail
from lhf.scraper.search import SearchCard
from lhf.scraper.shards import SEARCH_URL, SearchFilter

CHECKPOINT_VERSION = 1
type Phase = Literal["search", "details"]


@dataclass(slots=True)
class ActiveShard:
    filter: SearchFilter
    next_index: int


@dataclass(slots=True)
class Checkpoint:
    version: int
    min_price: int
    max_price: int
    max_pages: int | None
    min_bedrooms: int | None
    property_types: tuple[str, ...] | None
    tenure: str | None
    search_url_base: str
    phase: Phase
    pages_used: int
    pending_filters: list[SearchFilter]
    active: ActiveShard | None
    cards: list[SearchCard]
    details: dict[str, PropertyDetail | None]


def checkpoint_path(database_path: str | Path) -> Path:
    return Path(f"{database_path}.scrape-checkpoint.json")


def new_checkpoint(
    min_price: int,
    max_price: int,
    max_pages: int | None,
    min_bedrooms: int | None = None,
    property_types: tuple[str, ...] | None = None,
    tenure: str | None = None,
) -> Checkpoint:
    return Checkpoint(
        version=CHECKPOINT_VERSION,
        min_price=min_price,
        max_price=max_price,
        max_pages=max_pages,
        min_bedrooms=min_bedrooms,
        property_types=property_types,
        tenure=tenure,
        search_url_base=SEARCH_URL,
        phase="search",
        pages_used=0,
        pending_filters=[
            SearchFilter(
                min_price=min_price,
                max_price=max_price,
                min_bedrooms=min_bedrooms,
                property_types=property_types,
                tenure=tenure,
            )
        ],
        active=None,
        cards=[],
        details={},
    )


def save_checkpoint(path: Path, state: Checkpoint) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(asdict(state), separators=(",", ":")), encoding="utf-8")
    os.replace(tmp, path)


def clear_checkpoint(path: Path) -> None:
    path.unlink(missing_ok=True)
    path.with_name(path.name + ".tmp").unlink(missing_ok=True)


def load_checkpoint(path: Path) -> Checkpoint:
    if not path.is_file():
        raise ValueError(f"no scrape checkpoint to resume at {path}")
    try:
        payload: object = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("scrape checkpoint is invalid") from exc
    try:
        data = _object(payload)
        version = data["version"]
    except (TypeError, KeyError) as exc:
        raise ValueError("scrape checkpoint is invalid") from exc
    if version != CHECKPOINT_VERSION:
        raise ValueError(f"scrape checkpoint version {version} is not supported")
    try:
        return _checkpoint_from_payload(data)
    except (TypeError, KeyError, ValueError) as exc:
        raise ValueError("scrape checkpoint is invalid") from exc


def _checkpoint_from_payload(data: dict[str, object]) -> Checkpoint:
    search_url_base = data["search_url_base"]
    if not isinstance(search_url_base, str) or search_url_base != SEARCH_URL:
        raise ValueError("scrape checkpoint is invalid")
    raw_phase = data["phase"]
    if raw_phase == "search":
        phase: Phase = "search"
    elif raw_phase == "details":
        phase = "details"
    else:
        raise ValueError("scrape checkpoint is invalid")
    details_raw = _object(data["details"])
    return Checkpoint(
        version=CHECKPOINT_VERSION,
        min_price=_int(data["min_price"]),
        max_price=_int(data["max_price"]),
        max_pages=_optional_int(data["max_pages"]),
        min_bedrooms=_optional_int(data.get("min_bedrooms")),
        property_types=_optional_str_tuple(data.get("property_types")),
        tenure=_optional_str(data.get("tenure")),
        search_url_base=search_url_base,
        phase=phase,
        pages_used=_int(data["pages_used"]),
        pending_filters=[_search_filter(item) for item in _array(data["pending_filters"])],
        active=_active_shard(data["active"]),
        cards=[_search_card(item) for item in _array(data["cards"])],
        details={key: _property_detail(value) for key, value in details_raw.items()},
    )


def _active_shard(raw: object) -> ActiveShard | None:
    if raw is None:
        return None
    data = _object(raw)
    return ActiveShard(filter=_search_filter(data["filter"]), next_index=_int(data["next_index"]))


def _search_filter(raw: object) -> SearchFilter:
    data = _object(raw)
    return SearchFilter(
        min_price=_int(data["min_price"]),
        max_price=_int(data["max_price"]),
        min_bedrooms=_optional_int(data["min_bedrooms"]),
        max_bedrooms=_optional_int(data["max_bedrooms"]),
        property_types=_optional_str_tuple(data.get("property_types")),
        tenure=_optional_str(data.get("tenure")),
    )


def _search_card(raw: object) -> SearchCard:
    data = _object(raw)
    return SearchCard(
        listing_id=_str(data["listing_id"]),
        url=_str(data["url"]),
        display_address=_optional_str(data["display_address"]),
        asking_price_gbp=_optional_int(data["asking_price_gbp"]),
        price_qualifier=_optional_str(data["price_qualifier"]),
        bedrooms=_optional_int(data["bedrooms"]),
        display_size=_optional_str(data["display_size"]),
        property_type=_optional_str(data.get("property_type")),
        property_sub_type=_optional_str(data.get("property_sub_type")),
        tenure_type=_optional_str(data["tenure_type"]),
        key_features=_optional_str(data.get("key_features")),
        description=_optional_str(data.get("description")),
        bathrooms=_optional_int(data.get("bathrooms")),
        latitude=_optional_float(data.get("latitude")),
        longitude=_optional_float(data.get("longitude")),
        nearest_stations=_nearest_stations(data.get("nearest_stations")),
        listing_update_reason=_optional_str(data.get("listing_update_reason")),
        listing_update_date=_optional_str(data.get("listing_update_date")),
        first_visible_date=_optional_str(data.get("first_visible_date")),
    )


def _property_detail(raw: object) -> PropertyDetail | None:
    if raw is None:
        return None
    data = _object(raw)
    return PropertyDetail(
        display_address=_optional_str(data["display_address"]),
        asking_price_gbp=_optional_int(data["asking_price_gbp"]),
        price_qualifier=_optional_str(data["price_qualifier"]),
        bedrooms=_optional_int(data["bedrooms"]),
        property_type=_optional_str(data.get("property_type")),
        property_sub_type=_optional_str(data.get("property_sub_type")),
        outcode=_optional_str(data["outcode"]),
        incode=_optional_str(data["incode"]),
        floor_area_sqm=_optional_float(data["floor_area_sqm"]),
        floor_area_sqft=_optional_float(data["floor_area_sqft"]),
        tenure_type=_optional_str(data["tenure_type"]),
        years_remaining_on_lease=_optional_int(data["years_remaining_on_lease"]),
        annual_service_charge_gbp=_optional_int(data["annual_service_charge_gbp"]),
        annual_ground_rent_gbp=_optional_int(data["annual_ground_rent_gbp"]),
        key_features=_optional_str(data.get("key_features")),
        description=_optional_str(data.get("description")),
        bathrooms=_optional_int(data.get("bathrooms")),
        garden=_optional_str(data.get("garden")),
        parking=_optional_str(data.get("parking")),
        latitude=_optional_float(data.get("latitude")),
        longitude=_optional_float(data.get("longitude")),
        nearest_stations=_nearest_stations(data.get("nearest_stations")),
        listing_update_reason=_optional_str(data.get("listing_update_reason")),
        listing_update_date=_optional_str(data.get("listing_update_date")),
        first_visible_date=_optional_str(data.get("first_visible_date")),
    )


def _nearest_stations(raw: object) -> tuple[NearestStation, ...] | None:
    if raw is None:
        return None
    items = _array(raw)
    if not items:
        return None
    return tuple(_nearest_station(item) for item in items)


def _nearest_station(raw: object) -> NearestStation:
    data = _object(raw)
    return NearestStation(
        name=_str(data["name"]),
        types=tuple(_str(item) for item in _array(data["types"])),
        distance=_optional_float(data["distance"]),
        unit=_optional_str(data["unit"]),
    )


def _object(raw: object) -> dict[str, object]:
    if not isinstance(raw, dict):
        raise TypeError("expected object")
    return {str(key): item for key, item in cast(dict[object, object], raw).items()}


def _array(raw: object) -> list[object]:
    if not isinstance(raw, list):
        raise TypeError("expected array")
    return list(cast(list[object], raw))


def _str(raw: object) -> str:
    if not isinstance(raw, str):
        raise TypeError("expected str")
    return raw


def _optional_str(raw: object) -> str | None:
    if raw is None:
        return None
    return _str(raw)


def _int(raw: object) -> int:
    if isinstance(raw, bool) or not isinstance(raw, int):
        raise TypeError("expected int")
    return raw


def _optional_int(raw: object) -> int | None:
    if raw is None:
        return None
    return _int(raw)


def _optional_str_tuple(raw: object) -> tuple[str, ...] | None:
    if raw is None:
        return None
    return tuple(_str(item) for item in _array(raw))


def _optional_float(raw: object) -> float | None:
    if raw is None:
        return None
    if isinstance(raw, bool) or not isinstance(raw, int | float):
        raise TypeError("expected number")
    return float(raw)
