from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, fields, is_dataclass
from pathlib import Path
from types import NoneType, UnionType
from typing import Any, Literal, TypeAliasType, Union, cast, get_args, get_origin, get_type_hints

from lhf.scraper.detail import PropertyDetail
from lhf.scraper.search import SearchCard
from lhf.scraper.shards import SEARCH_URL, SearchFilter

CHECKPOINT_VERSION = 2
type Phase = Literal["search", "details"]


@dataclass(slots=True)
class ActiveShard:
    filter: SearchFilter
    next_index: int


@dataclass(slots=True)
class Checkpoint:
    version: int
    window: SearchFilter
    max_pages: int | None
    search_url_base: str
    phase: Phase
    pages_used: int
    pending_filters: list[SearchFilter]
    active: ActiveShard | None
    cards: list[SearchCard]
    details: dict[str, PropertyDetail | None]


def checkpoint_path(database_path: str | Path) -> Path:
    return Path(f"{database_path}.scrape-checkpoint.json")


def new_checkpoint(window: SearchFilter, max_pages: int | None) -> Checkpoint:
    return Checkpoint(
        version=CHECKPOINT_VERSION,
        window=window,
        max_pages=max_pages,
        search_url_base=SEARCH_URL,
        phase="search",
        pages_used=0,
        pending_filters=[window],
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
        state = _from_asdict(Checkpoint, data)
    except (TypeError, KeyError, ValueError) as exc:
        raise ValueError("scrape checkpoint is invalid") from exc
    if state.search_url_base != SEARCH_URL:
        raise ValueError("scrape checkpoint is invalid")
    return state


def _from_asdict[T](cls: type[T], raw: object) -> T:
    if not is_dataclass(cls):
        raise TypeError("expected dataclass")
    data = _object(raw)
    hints = get_type_hints(cls)
    values: dict[str, object] = {}
    for field in fields(cast(Any, cls)):
        if field.name not in data:
            raise KeyError(field.name)
        values[field.name] = _coerce(hints[field.name], data[field.name])
    return cls(**cast(Any, values))


def _coerce(annotation: object, raw: object) -> object:
    annotation = _unwrap(annotation)
    origin = get_origin(annotation)
    args = get_args(annotation)
    if origin is UnionType or origin is Union:
        non_none = [argument for argument in args if argument is not NoneType]
        if raw is None:
            if len(non_none) != len(args):
                return None
            raise TypeError("expected value")
        if len(non_none) == 1:
            return _coerce(non_none[0], raw)
        raise TypeError("unsupported union")
    if origin is Literal:
        if raw not in args:
            raise ValueError("unsupported literal")
        return raw
    if origin is list:
        return [_coerce(args[0], item) for item in _array(raw)]
    if origin is tuple:
        member = args[0]
        if len(args) == 2 and args[1] is Ellipsis:
            return tuple(_coerce(member, item) for item in _array(raw))
        raise TypeError("unsupported tuple")
    if origin is dict:
        mapping = _object(raw)
        return {str(key): _coerce(args[1], value) for key, value in mapping.items()}
    if is_dataclass(annotation) and isinstance(annotation, type):
        return _from_asdict(annotation, raw)
    if annotation is str:
        if not isinstance(raw, str):
            raise TypeError("expected str")
        return raw
    if annotation is int:
        if isinstance(raw, bool) or not isinstance(raw, int):
            raise TypeError("expected int")
        return raw
    if annotation is float:
        if isinstance(raw, bool) or not isinstance(raw, int | float):
            raise TypeError("expected number")
        return float(raw)
    raise TypeError("unsupported annotation")


def _unwrap(annotation: object) -> object:
    while isinstance(annotation, TypeAliasType):
        annotation = annotation.__value__
    return annotation


def _object(raw: object) -> dict[str, object]:
    if not isinstance(raw, dict):
        raise TypeError("expected object")
    return {str(key): item for key, item in cast(dict[object, object], raw).items()}


def _array(raw: object) -> list[object]:
    if not isinstance(raw, list):
        raise TypeError("expected array")
    return list(cast(list[object], raw))
