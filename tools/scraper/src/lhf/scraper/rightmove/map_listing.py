from __future__ import annotations

import re

from lhf.listings.listing import ListingDraft, normalise_postcode
from lhf.scraper.rightmove.detail import PropertyDetail
from lhf.scraper.rightmove.search import SearchCard

LEASEHOLD_TENURES = frozenset({"LEASEHOLD", "SHARE_OF_FREEHOLD"})
SQFT_PER_SQM = 10.7639
_DISPLAY_SQM = re.compile(
    r"^\s*([\d,]+(?:\.\d+)?)\s*(?:sq\.?\s*m(?:etres?)?|sqm)\s*$",
    re.IGNORECASE,
)


def map_listing(search: SearchCard, detail: PropertyDetail | None) -> ListingDraft:
    data = detail or PropertyDetail()
    tenure_type = _prefer(data.tenure_type, search.tenure_type)
    return ListingDraft(
        source="rightmove",
        external_id=search.listing_id,
        url=search.url,
        display_address=_prefer(data.display_address, search.display_address),
        asking_price_gbp=_search_asking_price(search, data),
        price_qualifier=_prefer(data.price_qualifier, search.price_qualifier),
        bedrooms=_prefer(data.bedrooms, search.bedrooms),
        property_type=_prefer(data.property_type, search.property_type),
        property_sub_type=_prefer(data.property_sub_type, search.property_sub_type),
        postcode=_postcode(data),
        floor_area_sqm=_floor_area(search, data),
        tenure_type=tenure_type,
        years_remaining_on_lease=_lease_years(data, tenure_type),
        annual_service_charge_gbp=data.annual_service_charge_gbp,
        annual_ground_rent_gbp=data.annual_ground_rent_gbp,
        key_features=_prefer(data.key_features, search.key_features),
        description=_prefer(data.description, search.description),
        bathrooms=_prefer(data.bathrooms, search.bathrooms),
        garden=data.garden,
        parking=data.parking,
        latitude=_prefer(data.latitude, search.latitude),
        longitude=_prefer(data.longitude, search.longitude),
        nearest_stations=_prefer(data.nearest_stations, search.nearest_stations),
        listing_update_reason=_prefer(data.listing_update_reason, search.listing_update_reason),
        listing_update_date=_prefer(data.listing_update_date, search.listing_update_date),
        first_visible_date=_prefer(data.first_visible_date, search.first_visible_date),
    )


def _postcode(detail: PropertyDetail) -> str | None:
    if detail.outcode is None or detail.incode is None:
        return None
    try:
        return normalise_postcode(f"{detail.outcode} {detail.incode}")
    except ValueError:
        return None


def _floor_area(search: SearchCard, detail: PropertyDetail) -> float | None:
    if detail.floor_area_sqm is not None:
        return detail.floor_area_sqm
    if detail.floor_area_sqft is not None:
        return detail.floor_area_sqft / SQFT_PER_SQM
    if search.display_size is None:
        return None
    match = _DISPLAY_SQM.fullmatch(search.display_size)
    if match is None:
        return None
    return float(match.group(1).replace(",", ""))


def _lease_years(detail: PropertyDetail, tenure_type: str | None) -> int | None:
    if tenure_type not in LEASEHOLD_TENURES:
        return None
    years = detail.years_remaining_on_lease
    if years is None or years <= 0:
        return None
    return years


def _search_asking_price(search: SearchCard, detail: PropertyDetail) -> int | None:
    return _prefer(search.asking_price_gbp, detail.asking_price_gbp)


def _prefer[T](primary: T | None, fallback: T | None) -> T | None:
    return primary if primary is not None else fallback
