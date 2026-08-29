from __future__ import annotations

import json
from dataclasses import dataclass
from typing import cast

from lhf.listings.listing import NearestStation
from lhf.scraper.json_values import (
    as_coordinates,
    as_dict,
    as_display_texts,
    as_int,
    as_joined_lines,
    as_list,
    as_nearest_stations,
    as_numeric_int,
    as_optional_str,
    as_positive_int,
    as_positive_number,
)


@dataclass(frozen=True, slots=True)
class PropertyDetail:
    display_address: str | None = None
    asking_price_gbp: int | None = None
    price_qualifier: str | None = None
    bedrooms: int | None = None
    property_type: str | None = None
    property_sub_type: str | None = None
    outcode: str | None = None
    incode: str | None = None
    floor_area_sqm: float | None = None
    floor_area_sqft: float | None = None
    tenure_type: str | None = None
    years_remaining_on_lease: int | None = None
    annual_service_charge_gbp: int | None = None
    annual_ground_rent_gbp: int | None = None
    key_features: str | None = None
    description: str | None = None
    bathrooms: int | None = None
    garden: str | None = None
    parking: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    nearest_stations: tuple[NearestStation, ...] | None = None
    listing_update_reason: str | None = None
    listing_update_date: str | None = None
    first_visible_date: str | None = None


def parse_property_data(html: str) -> PropertyDetail:
    wrapper = _extract_page_model(html)
    data = wrapper["data"]
    if not isinstance(data, str):
        raise ValueError("window.__PAGE_MODEL is missing data")
    packed: object = json.loads(data)
    if not isinstance(packed, list) or not packed:
        raise ValueError("packed __PAGE_MODEL data is empty")
    model = _unpack(cast(list[object], packed))
    if not isinstance(model, dict):
        raise ValueError("unpacked __PAGE_MODEL is not an object")
    property_data = as_dict(model).get("propertyData")
    if not isinstance(property_data, dict):
        raise ValueError("unpacked __PAGE_MODEL is missing propertyData")
    return _property_detail(as_dict(property_data))


def _property_detail(raw: dict[str, object]) -> PropertyDetail:
    address = as_dict(raw.get("address"))
    tenure = as_dict(raw.get("tenure"))
    living_costs = as_dict(raw.get("livingCosts"))
    features = as_dict(raw.get("features"))
    latitude, longitude = as_coordinates(raw.get("location"))
    floor_area_sqm, floor_area_sqft = _floor_areas(raw.get("sizings"))
    years = as_int(tenure.get("yearsRemainingOnLease"))
    if years is None:
        years = as_int(raw.get("yearsRemainingOnLease"))
    return PropertyDetail(
        display_address=as_optional_str(address.get("displayAddress")),
        asking_price_gbp=as_positive_int(as_dict(raw.get("mortgageCalculator")).get("price")),
        price_qualifier=as_optional_str(as_dict(raw.get("prices")).get("displayPriceQualifier")),
        bedrooms=as_int(raw.get("bedrooms")),
        property_type=as_optional_str(raw.get("propertyType")),
        property_sub_type=as_optional_str(raw.get("propertySubType")),
        outcode=as_optional_str(address.get("outcode")),
        incode=as_optional_str(address.get("incode")),
        floor_area_sqm=floor_area_sqm,
        floor_area_sqft=floor_area_sqft,
        tenure_type=as_optional_str(tenure.get("tenureType")),
        years_remaining_on_lease=years,
        annual_service_charge_gbp=as_numeric_int(living_costs.get("annualServiceCharge")),
        annual_ground_rent_gbp=as_numeric_int(living_costs.get("annualGroundRent")),
        key_features=as_joined_lines(raw.get("keyFeatures")),
        description=as_optional_str(as_dict(raw.get("text")).get("description")),
        bathrooms=as_int(raw.get("bathrooms")),
        garden=as_display_texts(features.get("garden")),
        parking=as_display_texts(features.get("parking")),
        latitude=latitude,
        longitude=longitude,
        nearest_stations=as_nearest_stations(raw.get("nearestStations")),
        listing_update_reason=as_optional_str(
            as_dict(raw.get("listingHistory")).get("listingUpdateReason")
        ),
        listing_update_date=as_optional_str(
            as_dict(raw.get("listingUpdate")).get("listingUpdateDate")
        ),
        first_visible_date=as_optional_str(raw.get("firstVisibleDate")),
    )


def _floor_areas(sizings: object) -> tuple[float | None, float | None]:
    sqm: float | None = None
    sqft: float | None = None
    for item in as_list(sizings):
        sizing = as_dict(item)
        area: float | None = None
        for key in ("maximumSize", "minimumSize", "maximum", "minimum"):
            area = as_positive_number(sizing.get(key))
            if area is not None:
                break
        if area is None:
            continue
        unit = (as_optional_str(sizing.get("unit")) or "").lower().replace(".", "").replace(" ", "")
        if unit == "sqm":
            sqm = area
        elif unit == "sqft":
            sqft = area
    return sqm, sqft


def _extract_page_model(html: str) -> dict[str, object]:
    marker = "window.__PAGE_MODEL"
    start = html.find(marker)
    if start == -1:
        raise ValueError("detail page is missing window.__PAGE_MODEL")
    equals = html.find("=", start + len(marker))
    if equals == -1:
        raise ValueError("detail page has a malformed window.__PAGE_MODEL")
    wrapper, _ = json.JSONDecoder().raw_decode(html[equals + 1 :].lstrip())
    mapping = as_dict(wrapper)
    if not isinstance(mapping.get("data"), str):
        raise ValueError("window.__PAGE_MODEL is missing data")
    return mapping


def _unpack(packed: list[object]) -> object:
    root = packed[0]
    memo: dict[int, object] = {}

    def resolve(idx: object, stack: set[int] | None = None) -> object:
        if stack is None:
            stack = set()
        if not isinstance(idx, int):
            return idx
        if idx in memo:
            return memo[idx]
        if idx in stack or idx < 0 or idx >= len(packed):
            return None if idx in stack else idx
        stack.add(idx)
        node = packed[idx]
        if isinstance(node, dict):
            out: object = {key: resolve(value, stack) for key, value in as_dict(node).items()}
        elif isinstance(node, list):
            out = [resolve(value, stack) for value in cast(list[object], node)]
        else:
            out = node
        stack.remove(idx)
        memo[idx] = out
        return out

    if isinstance(root, dict):
        return {key: resolve(value) for key, value in as_dict(root).items()}
    return resolve(0)
