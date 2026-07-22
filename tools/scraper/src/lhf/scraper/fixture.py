from __future__ import annotations

import json
from pathlib import Path
from typing import cast

from lhf.db.session import create_session_factory
from lhf.listings.listing import ListingDraft
from lhf.listings.listing_repository import ListingRepository


def load_fixture(fixture_path: str | Path) -> list[ListingDraft]:
    document = cast(object, json.loads(Path(fixture_path).read_text(encoding="utf-8")))
    if not isinstance(document, list):
        raise ValueError("fixture root must be a JSON array")

    items = cast(list[object], document)
    return [_parse_listing(item, index) for index, item in enumerate(items)]


def import_fixture(fixture_path: str | Path, database_path: str | Path) -> int:
    repository = ListingRepository(create_session_factory(database_path))
    return repository.upsert(load_fixture(fixture_path))


def _parse_listing(item: object, index: int) -> ListingDraft:
    if not isinstance(item, dict):
        raise ValueError(f"fixture item {index} must be a JSON object")
    values = cast(dict[object, object], item)
    floor_area = values.get("floor_area_sqm")
    if floor_area is not None and (
        isinstance(floor_area, bool) or not isinstance(floor_area, int | float)
    ):
        raise ValueError(f"fixture item {index}.floor_area_sqm must be a number or null")

    return ListingDraft(
        source=_required_string(values, "source", index),
        external_id=_required_string(values, "external_id", index),
        title=_required_string(values, "title", index),
        asking_price_gbp=_required_integer(values, "asking_price_gbp", index),
        postcode=_required_string(values, "postcode", index),
        url=_required_string(values, "url", index),
        floor_area_sqm=float(floor_area) if floor_area is not None else None,
    )


def _required_string(values: dict[object, object], field: str, index: int) -> str:
    value = values.get(field)
    if not isinstance(value, str):
        raise ValueError(f"fixture item {index}.{field} must be a string")
    return value


def _required_integer(values: dict[object, object], field: str, index: int) -> int:
    value = values.get(field)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"fixture item {index}.{field} must be an integer")
    return value
