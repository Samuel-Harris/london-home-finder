from __future__ import annotations

import json
import re
from dataclasses import dataclass

from lhf.listings.listing import NearestStation, normalise_postcode
from lhf.scraper.onthemarket.json_values import (
    as_dict,
    as_int,
    as_joined_features,
    as_lat_lon,
    as_list,
    as_nearest_stations,
    as_optional_str,
    as_positive_int,
    extract_next_data,
    nested,
)

_POSTCODE_TOKEN = re.compile(
    r"\b([A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2})\b",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class PropertyDetail:
    listing_id: str
    url: str
    display_address: str | None = None
    asking_price_gbp: int | None = None
    price_qualifier: str | None = None
    bedrooms: int | None = None
    bathrooms: int | None = None
    property_type: str | None = None
    property_sub_type: str | None = None
    postcode: str | None = None
    tenure_type: str | None = None
    key_features: str | None = None
    description: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    nearest_stations: tuple[NearestStation, ...] | None = None
    listing_update_reason: str | None = None


def parse_detail_page(html: str) -> PropertyDetail:
    payload = extract_next_data(html, page="detail page")
    property_data = nested(payload, "props", "initialReduxState", "property")
    if not isinstance(property_data, dict):
        raise ValueError("detail page is missing property")
    return _property_detail(as_dict(property_data))


def _property_detail(raw: dict[str, object]) -> PropertyDetail:
    listing_id = _identity_id(raw.get("id"))
    url = as_optional_str(raw.get("canonicalUrl"))
    if listing_id is None or url is None:
        raise ValueError("detail page is missing identity")
    latitude, longitude = as_lat_lon(raw.get("location"))
    display_address = as_optional_str(raw.get("displayAddress"))
    description = as_optional_str(raw.get("description")) or as_optional_str(raw.get("summary"))
    return PropertyDetail(
        listing_id=listing_id,
        url=url,
        display_address=display_address,
        asking_price_gbp=as_positive_int(raw.get("priceRaw")),
        price_qualifier=as_optional_str(raw.get("priceQualifier")),
        bedrooms=as_int(raw.get("bedrooms")),
        bathrooms=as_int(raw.get("bathrooms")),
        property_type=as_optional_str(raw.get("humanisedPropertyType")),
        property_sub_type=as_optional_str(raw.get("propSubId")),
        postcode=_postcode(raw.get("headerData"), display_address),
        tenure_type=_tenure_from_key_info(raw.get("keyInfo")),
        key_features=as_joined_features(raw.get("features")),
        description=description,
        latitude=latitude,
        longitude=longitude,
        nearest_stations=as_nearest_stations(raw.get("station")),
        listing_update_reason=as_optional_str(raw.get("daysSinceAddedReduced")),
    )


def _identity_id(value: object) -> str | None:
    text = as_optional_str(value)
    if text is not None:
        return text
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return str(value)


def _tenure_from_key_info(value: object) -> str | None:
    for item in as_list(value):
        raw = as_dict(item)
        if as_optional_str(raw.get("title")) != "Tenure":
            continue
        tenure = as_optional_str(raw.get("value"))
        if tenure is None or tenure.lower() == "ask agent":
            return None
        return tenure
    return None


def _postcode(header_data: object, display_address: str | None) -> str | None:
    header = as_dict(header_data)
    layer = as_optional_str(header.get("dataLayer"))
    if layer is not None:
        normalised = _normalise_postcode(_data_layer_postcode(layer))
        if normalised is not None:
            return normalised
    if display_address is None:
        return None
    match = _POSTCODE_TOKEN.search(display_address)
    if match is None:
        return None
    return _normalise_postcode(match.group(1))


def _data_layer_postcode(layer: str) -> str | None:
    try:
        payload: object = json.loads(layer)
    except json.JSONDecodeError:
        return None
    return as_optional_str(as_dict(payload).get("postcode"))


def _normalise_postcode(value: str | None) -> str | None:
    if value is None:
        return None
    try:
        return normalise_postcode(value)
    except ValueError:
        return None
