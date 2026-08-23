from __future__ import annotations

from collections.abc import Iterable

from lhf.listings._listing_row import ListingRow
from lhf.listings.listing import Listing, ListingDraft
from lhf.repository.protocol import Repository
from sqlalchemy import delete, select
from sqlalchemy.orm import Session, sessionmaker


class ListingRepository(Repository[ListingDraft, Listing]):
    def __init__(self, sessions: sessionmaker[Session]) -> None:
        self._sessions = sessions

    def replace_all(self, drafts: Iterable[ListingDraft]) -> int:
        draft_list = list(drafts)
        with self._sessions.begin() as session:
            session.execute(delete(ListingRow))
            session.add_all([_row_from_draft(draft) for draft in draft_list])
        return len(draft_list)

    def list_all(self) -> list[Listing]:
        with self._sessions() as session:
            rows = session.scalars(select(ListingRow).order_by(ListingRow.id)).all()
            return [_listing_from_row(row) for row in rows]


def _row_from_draft(draft: ListingDraft) -> ListingRow:
    return ListingRow(
        source=draft.source,
        external_id=draft.external_id,
        url=draft.url,
        display_address=draft.display_address,
        asking_price_gbp=draft.asking_price_gbp,
        price_qualifier=draft.price_qualifier,
        bedrooms=draft.bedrooms,
        postcode=draft.postcode,
        floor_area_sqm=draft.floor_area_sqm,
        tenure_type=draft.tenure_type,
        years_remaining_on_lease=draft.years_remaining_on_lease,
        annual_service_charge_gbp=draft.annual_service_charge_gbp,
        annual_ground_rent_gbp=draft.annual_ground_rent_gbp,
    )


def _listing_from_row(row: ListingRow) -> Listing:
    return Listing(
        id=row.id,
        source=row.source,
        external_id=row.external_id,
        url=row.url,
        display_address=row.display_address,
        asking_price_gbp=row.asking_price_gbp,
        price_qualifier=row.price_qualifier,
        bedrooms=row.bedrooms,
        postcode=row.postcode,
        floor_area_sqm=row.floor_area_sqm,
        tenure_type=row.tenure_type,
        years_remaining_on_lease=row.years_remaining_on_lease,
        annual_service_charge_gbp=row.annual_service_charge_gbp,
        annual_ground_rent_gbp=row.annual_ground_rent_gbp,
    )
