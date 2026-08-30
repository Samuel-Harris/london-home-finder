from __future__ import annotations

import sys
from pathlib import Path

from lhf.db.session import create_session_factory
from lhf.listings.listing_repository import ListingRepository
from lhf.scraper.checkpoint import (
    ActiveShard,
    Checkpoint,
    checkpoint_path,
    clear_checkpoint,
    load_checkpoint,
    new_checkpoint,
    save_checkpoint,
)
from lhf.scraper.detail import PropertyDetail, parse_property_data
from lhf.scraper.http import RIGHTMOVE_ORIGIN, Fetcher, FetchError
from lhf.scraper.map_listing import map_listing
from lhf.scraper.search import SearchCard, SearchPage, parse_search_page
from lhf.scraper.shards import SearchFilter, filter_label, search_url, split_filter
from lhf.scraper.window import DEFAULT_WINDOW, IngestWindow

MAX_SEARCH_INDEX = 984
SEARCH_PAGE_SIZE = 24
PAGE_RESULT_CAP = 1008


def scrape(
    database_path: str | Path,
    *,
    window: IngestWindow = DEFAULT_WINDOW,
    max_pages: int | None = None,
    resume: bool = False,
) -> int:
    _validate_max_pages(max_pages)
    search_filter = _search_filter(window)
    path = checkpoint_path(database_path)
    state = _load_or_start(path, search_filter, max_pages, resume)
    with Fetcher() as fetcher:
        _walk_search(fetcher, state, path)
        _walk_details(fetcher, state, path)
    drafts = [map_listing(card, state.details[card.listing_id]) for card in state.cards]
    if not drafts:
        raise ValueError("scrape produced no listings")
    count = ListingRepository(create_session_factory(database_path)).replace_all(drafts)
    clear_checkpoint(path)
    return count


def _search_filter(window: IngestWindow) -> SearchFilter:
    return SearchFilter(
        min_price=window.min_price,
        max_price=window.max_price,
        min_bedrooms=window.min_bedrooms,
        property_types=window.property_types,
        tenure=window.tenure,
    )


def _validate_max_pages(max_pages: int | None) -> None:
    if max_pages is not None and max_pages <= 0:
        raise ValueError("max_pages must be positive")


def _load_or_start(
    path: Path,
    search_filter: SearchFilter,
    max_pages: int | None,
    resume: bool,
) -> Checkpoint:
    if resume:
        state = load_checkpoint(path)
        if state.window != search_filter or state.max_pages != max_pages:
            raise ValueError(
                "scrape checkpoint does not match "
                f"min_price={search_filter.min_price} max_price={search_filter.max_price} "
                f"max_pages={max_pages!r} min_bedrooms={search_filter.min_bedrooms!r} "
                f"property_types={search_filter.property_types!r} tenure={search_filter.tenure!r}"
            )
        print(_resume_banner(state), file=sys.stderr)
        return state
    if path.exists():
        print(f"warning: discarding incomplete scrape checkpoint at {path}", file=sys.stderr)
    clear_checkpoint(path)
    state = new_checkpoint(search_filter, max_pages)
    save_checkpoint(path, state)
    return state


def _resume_banner(state: Checkpoint) -> str:
    line = (
        f"resuming scrape phase={state.phase} pages_used={state.pages_used} "
        f"cards={len(state.cards)} pending={len(state.pending_filters)}"
    )
    if state.active is not None:
        line += f" active={filter_label(state.active.filter)} next_index={state.active.next_index}"
    return line


def _walk_search(fetcher: Fetcher, state: Checkpoint, path: Path) -> None:
    if state.phase != "search":
        return
    pending = state.pending_filters
    while True:
        if state.max_pages is not None and state.pages_used >= state.max_pages:
            break
        if state.active is None:
            if not pending:
                break
            state.active = ActiveShard(filter=pending.pop(0), next_index=0)
        page = _search_page(fetcher, state.active.filter, state.active.next_index)
        if not page.properties:
            state.active = None
            save_checkpoint(path, state)
            continue
        if state.active.next_index == 0:
            if _shard_overflows(fetcher, state.active.filter, page):
                try:
                    lower, upper = split_filter(state.active.filter)
                except ValueError as exc:
                    raise FetchError(
                        "search still exceeds "
                        f"{PAGE_RESULT_CAP} listings for unsplittable filter "
                        f"({filter_label(state.active.filter)})"
                    ) from exc
                pending[:0] = [lower, upper]
                state.active = None
                save_checkpoint(path, state)
                continue
            print(
                f"shard {filter_label(state.active.filter)} resultCount={page.result_count}",
                file=sys.stderr,
            )
        _append_unique_in_band(state.cards, page.properties, state.window)
        state.pages_used += 1
        state.active.next_index += SEARCH_PAGE_SIZE
        if state.active.next_index > MAX_SEARCH_INDEX:
            state.active = None
        save_checkpoint(path, state)
    state.phase = "details"
    state.pending_filters = []
    state.active = None
    save_checkpoint(path, state)


def _walk_details(fetcher: Fetcher, state: Checkpoint, path: Path) -> None:
    for card in state.cards:
        if card.listing_id in state.details:
            continue
        state.details[card.listing_id] = _fetch_detail(fetcher, card)
        save_checkpoint(path, state)


def _append_unique_in_band(
    cards: list[SearchCard], incoming: list[SearchCard], search_filter: SearchFilter
) -> None:
    seen = {card.listing_id for card in cards}
    for card in _in_band(incoming, search_filter):
        if card.listing_id in seen:
            continue
        seen.add(card.listing_id)
        cards.append(card)


def _shard_overflows(fetcher: Fetcher, search_filter: SearchFilter, page: SearchPage) -> bool:
    if page.result_count is not None:
        return page.result_count > PAGE_RESULT_CAP
    last_page = _search_page(fetcher, search_filter, MAX_SEARCH_INDEX)
    return bool(last_page.properties)


def _search_page(fetcher: Fetcher, search_filter: SearchFilter, index: int) -> SearchPage:
    try:
        return parse_search_page(fetcher.get(search_url(search_filter, index)))
    except ValueError as exc:
        raise FetchError(str(exc)) from exc


def _in_band(cards: list[SearchCard], search_filter: SearchFilter) -> list[SearchCard]:
    return [
        card
        for card in cards
        if card.asking_price_gbp is None
        or search_filter.min_price <= card.asking_price_gbp <= search_filter.max_price
    ]


def _fetch_detail(fetcher: Fetcher, card: SearchCard) -> PropertyDetail | None:
    url = f"{RIGHTMOVE_ORIGIN}/properties/{card.listing_id}"
    try:
        return parse_property_data(fetcher.get(url))
    except (FetchError, ValueError) as exc:
        print(f"warning: failed to fetch detail for {card.listing_id}: {exc}", file=sys.stderr)
        return None
