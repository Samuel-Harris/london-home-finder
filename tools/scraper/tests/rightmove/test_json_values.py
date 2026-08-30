from lhf.listings.listing import NearestStation
from lhf.scraper.rightmove.json_values import (
    as_coordinates,
    as_display_texts,
    as_joined_lines,
    as_nearest_stations,
    as_number,
)


def test_as_joined_lines_joins_strings_and_skips_blanks() -> None:
    assert as_joined_lines(["Private garden", "  ", "Lift"]) == "Private garden\nLift"


def test_as_joined_lines_reads_search_card_description_objects() -> None:
    assert (
        as_joined_lines(
            [
                {"order": 2, "description": "Period features"},
                {"order": 1, "description": "Rear garden"},
            ]
        )
        == "Period features\nRear garden"
    )


def test_as_joined_lines_treats_empty_as_missing() -> None:
    assert as_joined_lines(None) is None
    assert as_joined_lines([]) is None
    assert as_joined_lines([{"order": 1, "description": "  "}]) is None


def test_as_display_texts_joins_feature_display_text() -> None:
    assert as_display_texts([{"alias": "yes", "displayText": "Yes"}]) == "Yes"
    assert (
        as_display_texts(
            [
                {"alias": "allocated", "displayText": "Allocated underground"},
                {"alias": "permit", "displayText": "Residents permit"},
            ]
        )
        == "Allocated underground\nResidents permit"
    )


def test_as_display_texts_treats_empty_as_missing() -> None:
    assert as_display_texts(None) is None
    assert as_display_texts([]) is None
    assert as_display_texts([{"alias": "yes", "displayText": "  "}]) is None


def test_as_number_keeps_negative_longitude() -> None:
    assert as_number(-0.1416) == -0.1416
    assert as_number(51.501) == 51.501
    assert as_number(True) is None


def test_as_coordinates_reads_location_object() -> None:
    assert as_coordinates({"latitude": 51.501, "longitude": -0.1416}) == (51.501, -0.1416)
    assert as_coordinates(None) == (None, None)


def test_as_nearest_stations_keeps_every_station_and_type() -> None:
    assert as_nearest_stations(
        [
            {
                "name": "Westminster Station",
                "types": ["LONDON_UNDERGROUND", "NATIONAL_TRAIN"],
                "distance": 0.15,
                "unit": "miles",
            },
            {
                "name": "Waterloo Station",
                "types": ["NATIONAL_TRAIN"],
                "distance": 0.8,
                "unit": "miles",
            },
        ]
    ) == (
        NearestStation(
            name="Westminster Station",
            types=("LONDON_UNDERGROUND", "NATIONAL_TRAIN"),
            distance=0.15,
            unit="miles",
        ),
        NearestStation(
            name="Waterloo Station",
            types=("NATIONAL_TRAIN",),
            distance=0.8,
            unit="miles",
        ),
    )


def test_as_nearest_stations_skips_malformed_items() -> None:
    assert as_nearest_stations(
        [
            {"name": "  "},
            "not a station",
            {"name": "Westminster Station", "types": ["LONDON_UNDERGROUND", "  ", 1]},
        ]
    ) == (
        NearestStation(
            name="Westminster Station",
            types=("LONDON_UNDERGROUND",),
            distance=None,
            unit=None,
        ),
    )


def test_as_nearest_stations_treats_empty_as_missing() -> None:
    assert as_nearest_stations(None) is None
    assert as_nearest_stations([]) is None
