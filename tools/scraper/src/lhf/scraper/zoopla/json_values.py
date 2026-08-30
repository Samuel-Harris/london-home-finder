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


def as_tenure_label(value: object) -> str | None:
    label = as_optional_str(value)
    if label is None:
        return None
    upper = label.upper()
    if "FREEHOLD" in upper or "LEASEHOLD" in upper:
        return upper
    return None


def as_int(value: object) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


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


def as_coordinates(value: object) -> tuple[float | None, float | None]:
    location = as_dict(value)
    return as_number(location.get("latitude")), as_number(location.get("longitude"))


def as_stations(names: object, miles: object | None = None) -> tuple[NearestStation, ...] | None:
    name_list = as_list(names)
    mile_list = as_list(miles)
    stations: list[NearestStation] = []
    for index, item in enumerate(name_list):
        name = as_optional_str(item)
        if name is None:
            continue
        distance = as_number(mile_list[index]) if index < len(mile_list) else None
        stations.append(
            NearestStation(
                name=name,
                types=(),
                distance=distance,
                unit=None if distance is None else "miles",
            )
        )
    return tuple(stations) if stations else None
