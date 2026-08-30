from __future__ import annotations

from lhf.listings.listing import ListingDraft, normalise_postcode
from lhf.scraper.zoopla.detail import PropertyDetail
from lhf.scraper.zoopla.search import SearchCard

SQFT_PER_SQM = 10.7639


def map_listing(search: SearchCard, detail: PropertyDetail | None) -> ListingDraft:
    data = detail or PropertyDetail()
    return ListingDraft(
        source="zoopla",
        external_id=search.listing_id,
        url=search.url,
        display_address=_prefer(data.display_address, search.display_address),
        asking_price_gbp=_prefer(search.asking_price_gbp, data.asking_price_gbp),
        price_qualifier=_prefer(data.price_qualifier, search.price_qualifier),
        bedrooms=_prefer(data.bedrooms, search.bedrooms),
        property_type=_prefer(data.property_type, search.property_type),
        postcode=_postcode(data),
        floor_area_sqm=_floor_area(search, data),
        tenure_type=_prefer(data.tenure_type, search.tenure_type),
        key_features=_prefer(data.key_features, search.summary),
        description=_prefer(data.description, search.summary),
        bathrooms=_prefer(data.bathrooms, search.bathrooms),
        garden=data.garden,
        parking=data.parking,
        latitude=_prefer(data.latitude, search.latitude),
        longitude=_prefer(data.longitude, search.longitude),
        nearest_stations=data.nearest_stations,
        listing_update_reason=_prefer(data.listing_update_reason, search.listing_update_reason),
        first_visible_date=_prefer(data.first_visible_date, search.first_visible_date),
    )


def _postcode(detail: PropertyDetail) -> str | None:
    if detail.postcode is None:
        return None
    try:
        return normalise_postcode(detail.postcode)
    except ValueError:
        return None


def _floor_area(search: SearchCard, detail: PropertyDetail) -> float | None:
    sqft = _prefer(detail.floor_area_sqft, search.size_sqft)
    if sqft is None:
        return None
    return sqft / SQFT_PER_SQM


def _prefer[T](primary: T | None, fallback: T | None) -> T | None:
    return primary if primary is not None else fallback
