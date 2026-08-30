from __future__ import annotations

import sys
from pathlib import Path
from typing import Literal

from lhf.db.session import create_session_factory
from lhf.listings.listing_repository import ListingRepository
from lhf.scraper.onthemarket.checkpoint import (
    ActiveShard,
    Checkpoint,
    checkpoint_path,
    clear_checkpoint,
    load_checkpoint,
    new_checkpoint,
    save_checkpoint,
)
from lhf.scraper.onthemarket.detail import PropertyDetail, parse_detail_page
from lhf.scraper.onthemarket.http import EmptyPage, Fetcher, FetchError
from lhf.scraper.onthemarket.in_window import in_window
from lhf.scraper.onthemarket.map_listing import map_listing
from lhf.scraper.onthemarket.search import SearchCard, SearchPage, parse_search_page
from lhf.scraper.onthemarket.shards import (
    LAST_WORKING_PAGE,
    PAGE_RESULT_CAP,
    detail_url,
    filter_label,
    search_url,
    split_shard,
    window_property_kinds,
)
from lhf.scraper.window import DEFAULT_WINDOW, IngestWindow

type _FirstPage = Literal["empty", "overflow", "crawl"]


def scrape(
    database_path: str | Path,
    *,
    window: IngestWindow = DEFAULT_WINDOW,
    max_pages: int | None = None,
    resume: bool = False,
) -> int:
    _validate_max_pages(max_pages)
    window_property_kinds(window)
    path = checkpoint_path(database_path)
    state = _load_or_start(path, window, max_pages, resume)
    with Fetcher() as fetcher:
        _walk_search(fetcher, state, path)
        _walk_details(fetcher, state, path)
    drafts = [map_listing(card, state.details[card.listing_id]) for card in state.cards]
    drafts = [draft for draft in drafts if in_window(draft, window)]
    if not drafts:
        raise ValueError("scrape produced no listings")
    count = ListingRepository(create_session_factory(database_path)).replace_source(
        "onthemarket", drafts
    )
    clear_checkpoint(path)
    return count


def _validate_max_pages(max_pages: int | None) -> None:
    if max_pages is not None and max_pages <= 0:
        raise ValueError("max_pages must be positive")


def _load_or_start(
    path: Path,
    window: IngestWindow,
    max_pages: int | None,
    resume: bool,
) -> Checkpoint:
    if resume:
        state = load_checkpoint(path)
        if state.window != window or state.max_pages != max_pages:
            raise ValueError(
                "onthemarket scrape checkpoint does not match "
                f"min_price={window.min_price} max_price={window.max_price} "
                f"max_pages={max_pages!r} min_bedrooms={window.min_bedrooms!r} "
                f"property_types={window.property_types!r} tenure={window.tenure!r}"
            )
        print(_resume_banner(state), file=sys.stderr)
        return state
    if path.exists():
        print(
            f"warning: discarding incomplete onthemarket scrape checkpoint at {path}",
            file=sys.stderr,
        )
    clear_checkpoint(path)
    state = new_checkpoint(window, max_pages)
    save_checkpoint(path, state)
    return state


def _resume_banner(state: Checkpoint) -> str:
    line = (
        f"resuming onthemarket scrape phase={state.phase} pages_used={state.pages_used} "
        f"cards={len(state.cards)} pending={len(state.pending)}"
    )
    if state.active is not None:
        line += f" active={filter_label(state.active.filter)} next_page={state.active.next_page}"
    return line


def _walk_search(fetcher: Fetcher, state: Checkpoint, path: Path) -> None:
    if state.phase != "search":
        return
    pending = state.pending
    while True:
        if state.max_pages is not None and state.pages_used >= state.max_pages:
            break
        if state.active is None:
            if not pending:
                break
            state.active = ActiveShard(filter=pending.pop(0), next_page=1)
        try:
            html = fetcher.get(search_url(state.active.filter, state.active.next_page))
        except EmptyPage:
            state.active = None
            save_checkpoint(path, state)
            continue
        page = _search_page(html)
        if state.active.next_page == 1:
            action = _first_page(page)
            if action == "empty":
                state.active = None
                save_checkpoint(path, state)
                continue
            if action == "overflow":
                try:
                    children = split_shard(state.active.filter, state.window)
                except ValueError as exc:
                    raise FetchError(
                        "search still exceeds "
                        f"{PAGE_RESULT_CAP} listings for unsplittable shard "
                        f"({filter_label(state.active.filter)})"
                    ) from exc
                pending[:0] = list(children)
                state.active = None
                save_checkpoint(path, state)
                continue
            print(
                f"shard {filter_label(state.active.filter)} totalResults={page.total_results}",
                file=sys.stderr,
            )
        _append_unique(state.cards, page.properties, state.window)
        state.pages_used += 1
        if not page.properties or state.active.next_page >= LAST_WORKING_PAGE:
            state.active = None
        else:
            state.active.next_page += 1
        save_checkpoint(path, state)
    state.phase = "details"
    save_checkpoint(path, state)


def _first_page(page: SearchPage) -> _FirstPage:
    if not page.properties and page.total_results == 0:
        return "empty"
    if page.total_results > PAGE_RESULT_CAP:
        return "overflow"
    return "crawl"


def _walk_details(fetcher: Fetcher, state: Checkpoint, path: Path) -> None:
    for card in state.cards:
        if card.listing_id in state.details:
            continue
        state.details[card.listing_id] = _fetch_detail(fetcher, card)
        save_checkpoint(path, state)


def _append_unique(
    cards: list[SearchCard], incoming: list[SearchCard], window: IngestWindow
) -> None:
    seen = {card.listing_id for card in cards}
    for card in incoming:
        if card.listing_id in seen or not in_window(card, window):
            continue
        seen.add(card.listing_id)
        cards.append(card)


def _search_page(html: str) -> SearchPage:
    try:
        return parse_search_page(html)
    except ValueError as exc:
        raise FetchError(str(exc)) from exc


def _fetch_detail(fetcher: Fetcher, card: SearchCard) -> PropertyDetail | None:
    try:
        return parse_detail_page(fetcher.get(detail_url(card.listing_id)))
    except (EmptyPage, FetchError, ValueError) as exc:
        print(f"warning: failed to fetch detail for {card.listing_id}: {exc}", file=sys.stderr)
        return None
