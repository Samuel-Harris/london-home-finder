from __future__ import annotations

import json
import re

from lhf.scraper.zoopla.json_values import as_dict

_NEXT_F_PUSH = re.compile(r'self\.__next_f\.push\(\[1,"((?:\\.|[^"\\])*)"\]\)')
_RSC_REF = re.compile(r"^\$([0-9a-z]+)$")


def concat_next_f(html: str) -> str:
    parts: list[str] = []
    for match in _NEXT_F_PUSH.finditer(html):
        parts.append(json.loads(f'"{match.group(1)}"'))
    if not parts:
        raise ValueError("page is missing __next_f payload")
    return "".join(parts)


def decode_json_field(flight: str, field: str) -> object:
    marker = f'"{field}":'
    index = flight.find(marker)
    if index < 0:
        raise ValueError(f"page is missing {field}")
    payload, _end = json.JSONDecoder().raw_decode(flight, index + len(marker))
    return payload


def listing_data_object(flight: str) -> dict[str, object]:
    marker = '"__typename":"ListingData"'
    index = flight.find(marker)
    if index < 0:
        raise ValueError("page is missing ListingData")
    start = flight.rfind("{", 0, index + 1)
    if start < 0:
        raise ValueError("page is missing ListingData")
    payload, _end = json.JSONDecoder().raw_decode(flight, start)
    if not isinstance(payload, dict):
        raise ValueError("ListingData is not an object")
    return as_dict(payload)


def resolve_rsc_text(flight: str, value: object) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    if not stripped:
        return None
    match = _RSC_REF.fullmatch(stripped)
    if match is None:
        return stripped
    chunk = _rsc_chunk(flight, match.group(1))
    if chunk is None:
        return None
    comma = chunk.find(",")
    if comma < 0:
        return stripped
    text = chunk[comma + 1 :].strip()
    return text or None


def _rsc_chunk(flight: str, identifier: str) -> str | None:
    marker = f"\n{identifier}:"
    index = flight.find(marker)
    if index < 0:
        index = flight.find(f"{identifier}:")
        if index < 0:
            return None
        return flight[index + len(identifier) + 1 :]
    return flight[index + len(marker) :]
