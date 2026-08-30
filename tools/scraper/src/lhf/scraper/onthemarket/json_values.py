from __future__ import annotations

import json
import re
from typing import Any, cast

from lhf.listings.listing import NearestStation

_NEXT_DATA = re.compile(
    r'<script[^>]*id="__NEXT_DATA__"[^>]*>\s*(.*?)\s*</script>',
    re.DOTALL,
)
_DISPLAY_DISTANCE = re.compile(
    r"^\s*([\d.]+)\s*(mi|miles|km)\.?\s*$",
    re.IGNORECASE,
)


def extract_next_data(html: str, *, page: str) -> object:
    match = _NEXT_DATA.search(html)
    if match is None:
        raise ValueError(f"{page} is missing __NEXT_DATA__")
    return json.loads(match.group(1))


def nested(payload: object, *keys: str) -> object:
    current: object = payload
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = as_dict(current).get(key)
    return current


def as_dict(value: Any) -> dict[str, object]:
    if not isinstance(value, dict):
        return {}
    return {str(key): item for key, item in cast(dict[object, object], value).items()}


def as_list(value: object) -> list[object]:
    if not isinstance(value, list):
        return []
    return list(cast(list[object], value))


def as_optional_str(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


def as_int(value: object) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


def as_positive_int(value: object) -> int | None:
    number = as_number(value)
    if number is None or number <= 0:
        return None
    return int(number)


def as_number(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    return float(value)


def as_lat_lon(value: object) -> tuple[float | None, float | None]:
    location = as_dict(value)
    return as_number(location.get("lat")), as_number(location.get("lon"))


def as_joined_features(value: object, *, key: str = "feature") -> str | None:
    lines: list[str] = []
    for item in as_list(value):
        if isinstance(item, str):
            text = as_optional_str(item)
        else:
            text = as_optional_str(as_dict(item).get(key))
        if text is not None:
            lines.append(text)
    if not lines:
        return None
    return "\n".join(lines)


def as_display_price(value: object) -> int | None:
    text = as_optional_str(value)
    if text is None:
        return None
    lowered = text.lower()
    if "poa" in lowered or "on application" in lowered:
        return None
    digits = "".join(character for character in text if character.isdigit())
    if not digits:
        return None
    amount = int(digits)
    return amount if amount > 0 else None


def as_nearest_stations(value: object) -> tuple[NearestStation, ...] | None:
    stations: list[NearestStation] = []
    for item in as_list(value):
        station = _as_nearest_station(item)
        if station is not None:
            stations.append(station)
    return tuple(stations) if stations else None


def _as_nearest_station(value: object) -> NearestStation | None:
    raw = as_dict(value)
    name = as_optional_str(raw.get("name"))
    if name is None:
        return None
    types: list[str] = []
    for entry in as_list(raw.get("allNetworks")):
        text = as_optional_str(as_dict(entry).get("type"))
        if text is not None:
            types.append(text)
    distance, unit = _display_distance(raw.get("displayDistance"))
    return NearestStation(name=name, types=tuple(types), distance=distance, unit=unit)


def _display_distance(value: object) -> tuple[float | None, str | None]:
    text = as_optional_str(value)
    if text is None:
        return None, None
    match = _DISPLAY_DISTANCE.fullmatch(text)
    if match is None:
        return None, None
    return float(match.group(1)), match.group(2).lower()
