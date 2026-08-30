from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, fields
from typing import Any, cast

from lhf.listings._listing_row import ListingRow
from lhf.listings.listing import Listing, ListingDraft, nearest_stations_from_stored
from sqlalchemy import delete, select
from sqlalchemy.orm import Session, sessionmaker


class ListingRepository:
    def __init__(self, sessions: sessionmaker[Session]) -> None:
        self._sessions = sessions

    def replace_source(self, source: str, drafts: Iterable[ListingDraft]) -> int:
        if not source.strip():
            raise ValueError("source must not be blank")
        draft_list = list(drafts)
        mismatched = next((draft for draft in draft_list if draft.source != source), None)
        if mismatched is not None:
            raise ValueError(f"draft source {mismatched.source!r} does not match {source!r}")
        with self._sessions.begin() as session:
            session.execute(delete(ListingRow).where(ListingRow.source == source))
            session.add_all([_row_from_draft(draft) for draft in draft_list])
        return len(draft_list)

    def list_all(self) -> list[Listing]:
        with self._sessions() as session:
            rows = session.scalars(select(ListingRow).order_by(ListingRow.id)).all()
            return [_listing_from_row(row) for row in rows]


def _row_from_draft(draft: ListingDraft) -> ListingRow:
    payload = asdict(draft)
    stations = payload["nearest_stations"]
    payload["nearest_stations"] = None if not stations else list(stations)
    return ListingRow(**payload)


def _listing_from_row(row: ListingRow) -> Listing:
    values: dict[str, object] = {
        field.name: getattr(row, field.name)
        for field in fields(Listing)
        if field.name != "nearest_stations"
    }
    values["nearest_stations"] = nearest_stations_from_stored(row.nearest_stations)
    return Listing(**cast(Any, values))
