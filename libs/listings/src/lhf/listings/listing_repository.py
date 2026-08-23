from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict
from typing import cast

from lhf.listings._listing_row import ListingRow
from lhf.listings.listing import Listing, ListingDraft, NearestStation
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
        property_type=draft.property_type,
        property_sub_type=draft.property_sub_type,
        postcode=draft.postcode,
        floor_area_sqm=draft.floor_area_sqm,
        tenure_type=draft.tenure_type,
        years_remaining_on_lease=draft.years_remaining_on_lease,
        annual_service_charge_gbp=draft.annual_service_charge_gbp,
        annual_ground_rent_gbp=draft.annual_ground_rent_gbp,
        key_features=draft.key_features,
        description=draft.description,
        bathrooms=draft.bathrooms,
        garden=draft.garden,
        parking=draft.parking,
        latitude=draft.latitude,
        longitude=draft.longitude,
        nearest_stations=(
            [asdict(station) for station in draft.nearest_stations]
            if draft.nearest_stations is not None
            else None
        ),
        listing_update_reason=draft.listing_update_reason,
        listing_update_date=draft.listing_update_date,
        first_visible_date=draft.first_visible_date,
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
        property_type=row.property_type,
        property_sub_type=row.property_sub_type,
        postcode=row.postcode,
        floor_area_sqm=row.floor_area_sqm,
        tenure_type=row.tenure_type,
        years_remaining_on_lease=row.years_remaining_on_lease,
        annual_service_charge_gbp=row.annual_service_charge_gbp,
        annual_ground_rent_gbp=row.annual_ground_rent_gbp,
        key_features=row.key_features,
        description=row.description,
        bathrooms=row.bathrooms,
        garden=row.garden,
        parking=row.parking,
        latitude=row.latitude,
        longitude=row.longitude,
        nearest_stations=_stations_from_row(row.nearest_stations),
        listing_update_reason=row.listing_update_reason,
        listing_update_date=row.listing_update_date,
        first_visible_date=row.first_visible_date,
    )


def _stations_from_row(
    raw: list[dict[str, object]] | None,
) -> tuple[NearestStation, ...] | None:
    if not raw:
        return None
    return tuple(_station_from_row(item) for item in raw)


def _station_from_row(raw: dict[str, object]) -> NearestStation:
    name = raw.get("name")
    types = raw.get("types")
    distance = raw.get("distance")
    unit = raw.get("unit")
    if not isinstance(name, str):
        raise TypeError("nearest_station name must be a str")
    if not isinstance(types, list):
        raise TypeError("nearest_station types must be a list of str")
    parsed_types: list[str] = []
    for item in cast(list[object], types):
        if not isinstance(item, str):
            raise TypeError("nearest_station types must be a list of str")
        parsed_types.append(item)
    if distance is not None and (
        isinstance(distance, bool) or not isinstance(distance, int | float)
    ):
        raise TypeError("nearest_station distance must be a number")
    if unit is not None and not isinstance(unit, str):
        raise TypeError("nearest_station unit must be a str")
    return NearestStation(
        name=name,
        types=tuple(parsed_types),
        distance=None if distance is None else float(distance),
        unit=unit,
    )
