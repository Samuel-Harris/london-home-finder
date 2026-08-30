from __future__ import annotations

from lhf.listings.listing import ListingDraft
from lhf.scraper.onthemarket.detail import PropertyDetail
from lhf.scraper.onthemarket.search import SearchCard


def map_listing(search: SearchCard, detail: PropertyDetail | None) -> ListingDraft:
    return ListingDraft(
        source="onthemarket",
        external_id=search.listing_id,
        url=search.url,
        display_address=_prefer(
            None if detail is None else detail.display_address, search.display_address
        ),
        asking_price_gbp=_prefer(
            None if detail is None else detail.asking_price_gbp, search.asking_price_gbp
        ),
        price_qualifier=_prefer(
            None if detail is None else detail.price_qualifier, search.price_qualifier
        ),
        bedrooms=_prefer(None if detail is None else detail.bedrooms, search.bedrooms),
        property_type=_prefer(
            None if detail is None else detail.property_type, search.property_type
        ),
        property_sub_type=None if detail is None else detail.property_sub_type,
        postcode=None if detail is None else detail.postcode,
        tenure_type=_prefer(None if detail is None else detail.tenure_type, search.tenure_type),
        key_features=_prefer(None if detail is None else detail.key_features, search.key_features),
        description=None if detail is None else detail.description,
        bathrooms=_prefer(None if detail is None else detail.bathrooms, search.bathrooms),
        latitude=_prefer(None if detail is None else detail.latitude, search.latitude),
        longitude=_prefer(None if detail is None else detail.longitude, search.longitude),
        nearest_stations=None if detail is None else detail.nearest_stations,
        listing_update_reason=_prefer(
            None if detail is None else detail.listing_update_reason, search.listing_update_reason
        ),
    )


def _prefer[T](primary: T | None, fallback: T | None) -> T | None:
    return primary if primary is not None else fallback
