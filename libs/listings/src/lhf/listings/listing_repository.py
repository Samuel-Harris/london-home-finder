from __future__ import annotations

from collections.abc import Iterable

from lhf.listings._listing_row import ListingRow
from lhf.listings.listing import Listing, ListingDraft
from lhf.repository.protocol import Repository
from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import Session, sessionmaker


class ListingRepository(Repository[ListingDraft, Listing]):
    def __init__(self, sessions: sessionmaker[Session]) -> None:
        self._sessions = sessions

    def upsert(self, drafts: Iterable[ListingDraft]) -> int:
        draft_list = list(drafts)
        if not draft_list:
            return 0

        statement = insert(ListingRow).values(
            [
                {
                    "source": draft.source,
                    "external_id": draft.external_id,
                    "title": draft.title,
                    "asking_price_gbp": draft.asking_price_gbp,
                    "postcode": draft.postcode,
                    "url": draft.url,
                    "floor_area_sqm": draft.floor_area_sqm,
                }
                for draft in draft_list
            ]
        )
        statement = statement.on_conflict_do_update(
            index_elements=[ListingRow.source, ListingRow.external_id],
            set_={
                "title": statement.excluded.title,
                "asking_price_gbp": statement.excluded.asking_price_gbp,
                "postcode": statement.excluded.postcode,
                "url": statement.excluded.url,
                "floor_area_sqm": statement.excluded.floor_area_sqm,
            },
        )
        with self._sessions.begin() as session:
            session.execute(statement)
        return len(draft_list)

    def list_all(self) -> list[Listing]:
        with self._sessions() as session:
            rows = session.scalars(select(ListingRow).order_by(ListingRow.id)).all()
            return [_listing_from_row(row) for row in rows]


def _listing_from_row(row: ListingRow) -> Listing:
    return Listing(
        id=row.id,
        source=row.source,
        external_id=row.external_id,
        title=row.title,
        asking_price_gbp=row.asking_price_gbp,
        postcode=row.postcode,
        url=row.url,
        floor_area_sqm=row.floor_area_sqm,
    )
