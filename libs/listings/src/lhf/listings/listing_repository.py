from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, fields
from typing import Any, cast

from lhf.listings._listing_row import ListingRow
from lhf.listings._zoopla_listing_row import ZooplaListingRow
from lhf.listings.listing import Listing, ListingDraft, nearest_stations_from_stored
from sqlalchemy import delete, select
from sqlalchemy.orm import Session, sessionmaker


class ListingRepository:
    def __init__(self, sessions: sessionmaker[Session]) -> None:
        self._sessions = sessions

    def replace_all(self, drafts: Iterable[ListingDraft]) -> int:
        return self._replace(ListingRow, drafts)

    def replace_zoopla(self, drafts: Iterable[ListingDraft]) -> int:
        return self._replace(ZooplaListingRow, drafts)

    def list_all(self) -> list[Listing]:
        with self._sessions() as session:
            rightmove = session.scalars(select(ListingRow).order_by(ListingRow.id)).all()
            zoopla = session.scalars(select(ZooplaListingRow).order_by(ZooplaListingRow.id)).all()
            listings = [_listing_from_row(row) for row in rightmove]
            listings.extend(_listing_from_row(row) for row in zoopla)
            listings.sort(key=lambda listing: (listing.source, listing.external_id))
            return listings

    def _replace(
        self,
        row_type: type[ListingRow] | type[ZooplaListingRow],
        drafts: Iterable[ListingDraft],
    ) -> int:
        draft_list = list(drafts)
        with self._sessions.begin() as session:
            session.execute(delete(row_type))
            session.add_all([_row_from_draft(row_type, draft) for draft in draft_list])
        return len(draft_list)


def _row_from_draft(
    row_type: type[ListingRow] | type[ZooplaListingRow], draft: ListingDraft
) -> ListingRow | ZooplaListingRow:
    payload = asdict(draft)
    stations = payload["nearest_stations"]
    payload["nearest_stations"] = None if not stations else list(stations)
    return row_type(**payload)


def _listing_from_row(row: ListingRow | ZooplaListingRow) -> Listing:
    values: dict[str, object] = {
        field.name: getattr(row, field.name)
        for field in fields(Listing)
        if field.name != "nearest_stations"
    }
    values["nearest_stations"] = nearest_stations_from_stored(row.nearest_stations)
    return Listing(**cast(Any, values))
