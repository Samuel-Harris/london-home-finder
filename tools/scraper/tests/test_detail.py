from pathlib import Path

from lhf.scraper.detail import parse_property_data

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_property_data_unpacks_leasehold_charges() -> None:
    property_data = parse_property_data(
        (FIXTURES / "detail_leasehold.html").read_text(encoding="utf-8")
    )

    assert property_data.tenure_type == "LEASEHOLD"
    assert property_data.years_remaining_on_lease == 87
    assert property_data.annual_service_charge_gbp == 2400
    assert property_data.annual_ground_rent_gbp == 400
    assert property_data.floor_area_sqm == 58


def test_parse_property_data_unpacks_freehold_zero_lease_years() -> None:
    property_data = parse_property_data(
        (FIXTURES / "detail_freehold.html").read_text(encoding="utf-8")
    )

    assert property_data.tenure_type == "FREEHOLD"
    assert property_data.years_remaining_on_lease == 0
    assert property_data.outcode == "SW1A"
    assert property_data.incode == "2AA"
    assert property_data.floor_area_sqft == 700
    assert property_data.floor_area_sqm is None


def test_parse_property_data_reads_live_sizing_keys() -> None:
    html = (
        '<script>window.__PAGE_MODEL = {"data": '
        '"[{\\"propertyData\\":1},{\\"sizings\\":2},[3],'
        '{\\"unit\\":4,\\"minimumSize\\":5,\\"maximumSize\\":6},\\"sqm\\",50,72]", '
        '"encoding": "json"};</script>'
    )

    assert parse_property_data(html).floor_area_sqm == 72
