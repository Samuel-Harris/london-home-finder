from __future__ import annotations

from pathlib import Path

import pytest
from lhf.scraper.cli import main
from lhf.scraper.scrape import (
    DEFAULT_MAX_PRICE,
    DEFAULT_MIN_BEDROOMS,
    DEFAULT_MIN_PRICE,
    DEFAULT_PROPERTY_TYPES,
    DEFAULT_TENURE,
)


def test_cli_defaults_pass_the_default_search_window(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, object] = {}

    def fake_scrape(database: Path, **kwargs: object) -> int:
        captured["database"] = database
        captured.update(kwargs)
        return 0

    monkeypatch.setattr("lhf.scraper.cli.scrape", fake_scrape)
    database = tmp_path / "listings.sqlite3"
    assert main(["--database", str(database)]) == 0
    assert captured["database"] == database
    assert captured["min_price"] == DEFAULT_MIN_PRICE
    assert captured["max_price"] == DEFAULT_MAX_PRICE
    assert captured["min_bedrooms"] == DEFAULT_MIN_BEDROOMS
    assert captured["property_types"] == DEFAULT_PROPERTY_TYPES
    assert captured["tenure"] == DEFAULT_TENURE
    assert captured["resume"] is False


def test_cli_any_omits_optional_filters(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_scrape(database: Path, **kwargs: object) -> int:
        captured.update(kwargs)
        return 0

    monkeypatch.setattr("lhf.scraper.cli.scrape", fake_scrape)
    assert (
        main(
            [
                "--database",
                str(tmp_path / "listings.sqlite3"),
                "--min-bedrooms",
                "0",
                "--property-types",
                "any",
                "--tenure",
                "any",
            ]
        )
        == 0
    )
    assert captured["min_bedrooms"] is None
    assert captured["property_types"] is None
    assert captured["tenure"] is None
