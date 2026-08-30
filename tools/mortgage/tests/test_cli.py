from __future__ import annotations

import pytest
from lhf.mortgage_cli.cli import main


def _plain(output: str) -> str:
    return " ".join(output.split())


def test_price_prints_a_table(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["price", "--base-salary", "90000", "--cash", "40000", "--lisa", "10000"]) == 0
    output = _plain(capsys.readouterr().out)
    assert "Price" in output
    assert "Monthly" in output
    assert "August 2026" in output
    assert "not financial advice" in output


def test_missing_required_flags_fail() -> None:
    with pytest.raises(SystemExit):
        main(["price"])


def test_deposit_rejects_cash_flag() -> None:
    with pytest.raises(SystemExit):
        main(
            [
                "deposit",
                "--base-salary",
                "90000",
                "--price",
                "410000",
                "--cash",
                "40000",
            ]
        )


def test_deposit_rejects_term_flag() -> None:
    with pytest.raises(SystemExit):
        main(
            [
                "deposit",
                "--base-salary",
                "90000",
                "--price",
                "410000",
                "--term",
                "25",
            ]
        )


def test_non_positive_term_fails() -> None:
    with pytest.raises(SystemExit):
        main(
            [
                "monthly",
                "--base-salary",
                "90000",
                "--cash",
                "40000",
                "--price",
                "410000",
                "--term",
                "0",
            ]
        )


def test_monthly_cap_marks_later_rows_over_monthly(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert (
        main(
            [
                "price",
                "--base-salary",
                "90000",
                "--cash",
                "40000",
                "--lisa",
                "10000",
                "--monthly",
                "2200",
                "--min-price",
                "400000",
                "--max-price",
                "560000",
                "--step",
                "10000",
            ]
        )
        == 0
    )
    output = _plain(capsys.readouterr().out)
    assert "over monthly" in output
    assert "Highest viable price:" in output


def test_invalid_income_multiple_is_usage_error(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as caught:
        main(
            [
                "price",
                "--base-salary",
                "90000",
                "--cash",
                "40000",
                "--income-multiple",
                "foo",
            ]
        )
    assert caught.value.code == 2
    assert "invalid decimal value: 'foo'" in capsys.readouterr().err


def test_unsatisfiable_prints_reason_and_caveat(capsys: pytest.CaptureFixture[str]) -> None:
    assert (
        main(
            [
                "price",
                "--base-salary",
                "90000",
                "--cash",
                "1000",
                "--min-price",
                "2000000",
                "--max-price",
                "2100000",
                "--step",
                "10000",
            ]
        )
        == 1
    )
    output = _plain(capsys.readouterr().out)
    assert "No price in this range is viable." in output
    assert "August 2026" in output
    assert "not financial advice" in output
