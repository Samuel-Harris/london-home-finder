from pathlib import Path

from lhf.scraper.detail import parse_property_data

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_property_data_unpacks_leasehold_charges() -> None:
    property_data = parse_property_data(
        (FIXTURES / "detail_leasehold.html").read_text(encoding="utf-8")
    )

    assert property_data.tenure_type == "LEASEHOLD"
    assert property_data.property_type == "flat"
    assert property_data.property_sub_type == "Maisonette"
    assert property_data.years_remaining_on_lease == 87
    assert property_data.annual_service_charge_gbp == 2400
    assert property_data.annual_ground_rent_gbp == 400
    assert property_data.floor_area_sqm == 58
    assert property_data.key_features == "Private garden\nLift"
    assert property_data.description == "A leasehold maisonette.<br /><br />Private garden."
    assert property_data.bathrooms == 1
    assert property_data.garden == "Yes"
    assert property_data.parking == "Allocated underground"
    assert property_data.latitude == 51.501
    assert property_data.longitude == -0.1416
    assert property_data.listing_update_reason == "Reduced on 12/05/2026"
    assert [station.name for station in property_data.nearest_stations or ()] == [
        "Westminster Station",
        "Waterloo Station",
    ]
    assert property_data.nearest_stations is not None
    assert property_data.nearest_stations[0].types == ("LONDON_UNDERGROUND", "NATIONAL_TRAIN")


def test_parse_property_data_unpacks_freehold_zero_lease_years() -> None:
    property_data = parse_property_data(
        (FIXTURES / "detail_freehold.html").read_text(encoding="utf-8")
    )

    assert property_data.tenure_type == "FREEHOLD"
    assert property_data.property_type == "house"
    assert property_data.property_sub_type == "Terraced"
    assert property_data.years_remaining_on_lease == 0
    assert property_data.outcode == "SW1A"
    assert property_data.incode == "2AA"
    assert property_data.floor_area_sqft == 700
    assert property_data.floor_area_sqm is None
    assert property_data.key_features == "Rear garden\nPeriod features"
    assert property_data.description == "A terraced house in Westminster."
    assert property_data.bathrooms == 2
    assert property_data.garden == "Private garden"
    assert property_data.parking is None
    assert property_data.latitude == 51.5034
    assert property_data.longitude == -0.1276
    assert property_data.nearest_stations is None


def test_parse_property_data_reads_live_sizing_keys() -> None:
    html = (
        '<script>window.__PAGE_MODEL = {"data": '
        '"[{\\"propertyData\\":1},{\\"sizings\\":2},[3],'
        '{\\"unit\\":4,\\"minimumSize\\":5,\\"maximumSize\\":6},\\"sqm\\",50,72]", '
        '"encoding": "json"};</script>'
    )

    parsed = parse_property_data(html)
    assert parsed.floor_area_sqm == 72
    assert parsed.key_features is None
    assert parsed.description is None
