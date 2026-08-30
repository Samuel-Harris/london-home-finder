from __future__ import annotations

from dataclasses import dataclass

from lhf.listings.listing import NearestStation
from lhf.scraper.zoopla.flight import (
    concat_next_f,
    decode_json_field,
    listing_data_object,
    resolve_rsc_text,
)
from lhf.scraper.zoopla.json_values import (
    as_coordinates,
    as_dict,
    as_int,
    as_list,
    as_numeric_int,
    as_optional_str,
    as_positive_number,
    as_stations,
    as_tenure_label,
)


@dataclass(frozen=True, slots=True)
class PropertyDetail:
    display_address: str | None = None
    asking_price_gbp: int | None = None
    price_qualifier: str | None = None
    bedrooms: int | None = None
    bathrooms: int | None = None
    property_type: str | None = None
    postcode: str | None = None
    floor_area_sqft: float | None = None
    tenure_type: str | None = None
    key_features: str | None = None
    description: str | None = None
    garden: str | None = None
    parking: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    nearest_stations: tuple[NearestStation, ...] | None = None
    listing_update_reason: str | None = None
    first_visible_date: str | None = None


def parse_property_data(html: str) -> PropertyDetail:
    flight = concat_next_f(html)
    data = listing_data_object(flight)
    location = as_dict(data.get("location"))
    counts = as_dict(data.get("counts"))
    ingested = as_dict(data.get("ingested"))
    features = as_dict(data.get("features"))
    pricing = as_dict(data.get("pricing"))
    targeting = as_dict(data.get("adTargeting"))
    status = as_dict(data.get("statusSummary"))
    latitude, longitude = as_coordinates(location.get("coordinates"))
    bullets = _bullet_lines(features.get("bullets"))
    parking = _parking(data.get("additionalNtsInfo"))
    return PropertyDetail(
        display_address=as_optional_str(data.get("displayAddress")),
        asking_price_gbp=as_numeric_int(pricing.get("internalValue")),
        price_qualifier=as_optional_str(pricing.get("priceQualifierLabel")),
        bedrooms=as_int(counts.get("numBedrooms")),
        bathrooms=as_int(counts.get("numBathrooms")),
        property_type=as_optional_str(data.get("propertyType")),
        postcode=as_optional_str(location.get("postalCode")),
        floor_area_sqft=as_positive_number(ingested.get("sizeSqft")),
        tenure_type=_tenure(data.get("tagsV2"), targeting),
        key_features=bullets,
        description=resolve_rsc_text(flight, data.get("detailedDescription")),
        garden=_garden(bullets),
        parking=parking,
        latitude=latitude,
        longitude=longitude,
        nearest_stations=_stations(flight, data),
        listing_update_reason=as_optional_str(status.get("label")),
        first_visible_date=as_optional_str(data.get("publishedOn")),
    )


def _bullet_lines(value: object) -> str | None:
    lines: list[str] = []
    for item in as_list(value):
        text = as_optional_str(item)
        if text is not None:
            lines.append(text)
    if not lines:
        return None
    return "\n".join(lines)


def _garden(bullets: str | None) -> str | None:
    if bullets is None:
        return None
    matches = [line for line in bullets.split("\n") if "garden" in line.lower()]
    if not matches:
        return None
    return "\n".join(matches)


def _parking(value: object) -> str | None:
    for item in as_list(value):
        info = as_dict(item)
        if as_optional_str(info.get("key")) != "parking":
            continue
        text = as_optional_str(info.get("value"))
        if text is None or text.lower() == "ask agent":
            return None
        return text
    return None


def _stations(flight: str, data: dict[str, object]) -> tuple[NearestStation, ...] | None:
    listed = as_stations(data.get("nearestStations"), data.get("nearestStationsInMiles"))
    if listed is not None:
        return listed
    try:
        names = decode_json_field(flight, "nearestStations")
    except ValueError:
        return None
    try:
        miles = decode_json_field(flight, "nearestStationsInMiles")
    except ValueError:
        miles = None
    return as_stations(names, miles)


def _tenure(tags: object, targeting: dict[str, object]) -> str | None:
    for item in as_list(tags):
        tenure = as_tenure_label(as_dict(item).get("label"))
        if tenure is not None:
            return tenure
    return as_tenure_label(targeting.get("tenure"))
