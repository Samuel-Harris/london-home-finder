from __future__ import annotations

from pathlib import Path

import pytest
from lhf.scraper.cli import main
from lhf.scraper.window import DEFAULT_WINDOW, IngestWindow


def test_cli_defaults_pass_the_default_search_window(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, object] = {}

    def fake_scrape(database: Path, **kwargs: object) -> int:
        captured["database"] = database
        captured.update(kwargs)
        return 0

    monkeypatch.setattr("lhf.scraper.cli.scrape_rightmove", fake_scrape)
    database = tmp_path / "listings.sqlite3"
    assert main(["--database", str(database)]) == 0
    assert captured["database"] == database
    assert captured["window"] == DEFAULT_WINDOW
    assert captured["resume"] is False


def test_cli_any_omits_optional_filters(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_scrape(database: Path, **kwargs: object) -> int:
        captured.update(kwargs)
        return 0

    monkeypatch.setattr("lhf.scraper.cli.scrape_rightmove", fake_scrape)
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
    assert captured["window"] == IngestWindow(
        min_bedrooms=None,
        property_types=None,
        tenure=None,
    )


def test_cli_rejects_negative_min_bedrooms(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def fail(*_args: object, **_kwargs: object) -> int:
        raise AssertionError("scrape should not run")

    monkeypatch.setattr("lhf.scraper.cli.scrape_rightmove", fail)
    with pytest.raises(SystemExit) as caught:
        main(["--database", str(tmp_path / "listings.sqlite3"), "--min-bedrooms", "-1"])
    assert caught.value.code == 2
    assert "min_bedrooms" in capsys.readouterr().err


def test_cli_source_zoopla_dispatches_to_zoopla_scrape(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, object] = {}

    def fake_scrape(database: Path, **kwargs: object) -> int:
        captured["database"] = database
        captured.update(kwargs)
        return 0

    def fail(*_args: object, **_kwargs: object) -> int:
        raise AssertionError("rightmove scrape should not run")

    monkeypatch.setattr("lhf.scraper.cli.scrape_zoopla", fake_scrape)
    monkeypatch.setattr("lhf.scraper.cli.scrape_rightmove", fail)
    database = tmp_path / "listings.sqlite3"
    assert main(["--database", str(database), "--source", "zoopla"]) == 0
    assert captured["database"] == database
    assert captured["window"] == DEFAULT_WINDOW
    assert captured["resume"] is False
