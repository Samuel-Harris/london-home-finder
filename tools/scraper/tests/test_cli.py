from __future__ import annotations

from pathlib import Path

import pytest
from lhf.scraper.cli import main
from lhf.scraper.window import DEFAULT_WINDOW, IngestWindow


def test_cli_defaults_call_both_sources(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    captured: list[tuple[str, Path, dict[str, object]]] = []

    def fake_rightmove(database: Path, **kwargs: object) -> int:
        captured.append(("rightmove", database, kwargs))
        return 4

    def fake_onthemarket(database: Path, **kwargs: object) -> int:
        captured.append(("onthemarket", database, kwargs))
        return 2

    monkeypatch.setattr("lhf.scraper.cli.scrape_rightmove", fake_rightmove)
    monkeypatch.setattr("lhf.scraper.cli.scrape_onthemarket", fake_onthemarket)
    database = tmp_path / "listings.sqlite3"
    assert main(["--database", str(database)]) == 0
    assert [item[0] for item in captured] == ["rightmove", "onthemarket"]
    assert captured[0][1] == database
    assert captured[0][2]["window"] == DEFAULT_WINDOW
    assert captured[0][2]["resume"] is False
    assert captured[1][2]["window"] == DEFAULT_WINDOW
    assert captured[1][2]["resume"] is False
    stdout = capsys.readouterr().out
    assert f"Replaced rightmove listings with 4 rows in {database}." in stdout
    assert f"Replaced onthemarket listings with 2 rows in {database}." in stdout


def test_cli_any_omits_optional_filters(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    captured: list[object] = []

    def fake_scrape(database: Path, **kwargs: object) -> int:
        del database
        captured.append(kwargs["window"])
        return 0

    monkeypatch.setattr("lhf.scraper.cli.scrape_rightmove", fake_scrape)
    monkeypatch.setattr("lhf.scraper.cli.scrape_onthemarket", fake_scrape)
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
    expected = IngestWindow(
        min_bedrooms=None,
        property_types=None,
        tenure=None,
    )
    assert captured == [expected, expected]


def test_cli_resume_starts_later_source_if_earlier_still_in_progress(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    captured: list[tuple[str, bool]] = []

    def fake_rightmove(database: Path, **kwargs: object) -> int:
        del database
        captured.append(("rightmove", bool(kwargs["resume"])))
        return 1

    def fake_onthemarket(database: Path, **kwargs: object) -> int:
        del database
        captured.append(("onthemarket", bool(kwargs["resume"])))
        return 2

    monkeypatch.setattr("lhf.scraper.cli.scrape_rightmove", fake_rightmove)
    monkeypatch.setattr("lhf.scraper.cli.scrape_onthemarket", fake_onthemarket)
    database = tmp_path / "listings.sqlite3"
    (tmp_path / "listings.sqlite3.scrape-checkpoint.json").write_text("{}", encoding="utf-8")
    assert main(["--database", str(database), "--resume"]) == 0
    assert captured == [("rightmove", True), ("onthemarket", False)]
    stdout = capsys.readouterr().out
    assert f"Replaced rightmove listings with 1 rows in {database}." in stdout
    assert f"Replaced onthemarket listings with 2 rows in {database}." in stdout


def test_cli_resume_skips_source_without_checkpoint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    captured: list[str] = []

    def fake_rightmove(*_args: object, **_kwargs: object) -> int:
        raise AssertionError("rightmove should not run")

    def fake_onthemarket(database: Path, **kwargs: object) -> int:
        captured.append("onthemarket")
        assert kwargs["resume"] is True
        return 3

    monkeypatch.setattr("lhf.scraper.cli.scrape_rightmove", fake_rightmove)
    monkeypatch.setattr("lhf.scraper.cli.scrape_onthemarket", fake_onthemarket)
    database = tmp_path / "listings.sqlite3"
    checkpoint = tmp_path / "listings.sqlite3.onthemarket-scrape-checkpoint.json"
    checkpoint.write_text("{}", encoding="utf-8")
    assert main(["--database", str(database), "--resume"]) == 0
    assert captured == ["onthemarket"]
    stdout = capsys.readouterr().out
    assert "rightmove" not in stdout
    assert f"Replaced onthemarket listings with 3 rows in {database}." in stdout


def test_cli_resume_without_either_checkpoint_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def fail(*_args: object, **_kwargs: object) -> int:
        raise AssertionError("scrape should not run")

    monkeypatch.setattr("lhf.scraper.cli.scrape_rightmove", fail)
    monkeypatch.setattr("lhf.scraper.cli.scrape_onthemarket", fail)
    with pytest.raises(SystemExit) as caught:
        main(["--database", str(tmp_path / "listings.sqlite3"), "--resume"])
    assert caught.value.code == 2
    assert "no scrape checkpoint to resume" in capsys.readouterr().err


def test_cli_rejects_negative_min_bedrooms(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def fail(*_args: object, **_kwargs: object) -> int:
        raise AssertionError("scrape should not run")

    monkeypatch.setattr("lhf.scraper.cli.scrape_rightmove", fail)
    monkeypatch.setattr("lhf.scraper.cli.scrape_onthemarket", fail)
    with pytest.raises(SystemExit) as caught:
        main(["--database", str(tmp_path / "listings.sqlite3"), "--min-bedrooms", "-1"])
    assert caught.value.code == 2
    assert "min_bedrooms" in capsys.readouterr().err
