from __future__ import annotations

from typing import Any, cast

from lhf.listings.listing import NearestStation


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


def as_joined_lines(value: object) -> str | None:
    if isinstance(value, str):
        return as_optional_str(value)
    return _join_texts(value, "description")


def as_int(value: object) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


def as_positive_int(value: object) -> int | None:
    number = as_positive_number(value)
    if number is None:
        return None
    return int(number)


def as_numeric_int(value: object) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    return int(value)


def as_number(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    return float(value)


def as_positive_number(value: object) -> float | None:
    number = as_number(value)
    if number is None or number <= 0:
        return None
    return number


def as_display_texts(value: object) -> str | None:
    return _join_texts(value, "displayText")


def _join_texts(value: object, key: str) -> str | None:
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


def as_coordinates(value: object) -> tuple[float | None, float | None]:
    location = as_dict(value)
    return as_number(location.get("latitude")), as_number(location.get("longitude"))


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
    for entry in as_list(raw.get("types")):
        text = as_optional_str(entry)
        if text is not None:
            types.append(text)
    return NearestStation(
        name=name,
        types=tuple(types),
        distance=as_number(raw.get("distance")),
        unit=as_optional_str(raw.get("unit")),
    )
