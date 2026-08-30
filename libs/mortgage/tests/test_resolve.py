from __future__ import annotations

from lhf.mortgage.buyer import Buyer, Earnings, Funds
from lhf.mortgage.enquiry import (
    DepositAnswer,
    DepositAtPrice,
    IncomeAnswer,
    IncomeAtPrice,
    PriceTableAnswer,
    PriceUnknown,
    PriceUnknownCappedByMonthly,
    Unsatisfiable,
    resolve,
)
from lhf.mortgage.evaluate import evaluate_at_price
from lhf.mortgage.snapshot import AUGUST_2026


def test_monthly_cap_reverses_near_four_hundred_ten_thousand(sample_buyer: Buyer) -> None:
    answer = resolve(
        PriceUnknownCappedByMonthly(buyer=sample_buyer, monthly=2_200),
        AUGUST_2026,
    )

    assert isinstance(answer, PriceTableAnswer)
    assert abs(answer.max_viable.price - 410_000) <= 5_000
    assert answer.max_viable.monthly is not None
    assert answer.max_viable.monthly <= 2_200
    assert answer.max_viable in answer.rows
    assert answer.caveat == AUGUST_2026.caveat


def test_price_unknown_densifies_to_true_max(sample_buyer: Buyer) -> None:
    answer = resolve(
        PriceUnknown(buyer=sample_buyer, min_price=430_000, max_price=460_000, step=10_000),
        AUGUST_2026,
    )

    assert isinstance(answer, PriceTableAnswer)
    assert answer.max_viable.price == 445_238
    assert answer.max_viable in answer.rows
    assert evaluate_at_price(AUGUST_2026, sample_buyer, 445_239).constraints.viable is False


def test_price_unknown_returns_last_viable_row(sample_buyer: Buyer) -> None:
    answer = resolve(
        PriceUnknown(buyer=sample_buyer, min_price=350_000, max_price=420_000, step=10_000),
        AUGUST_2026,
    )

    assert isinstance(answer, PriceTableAnswer)
    viable = tuple(row for row in answer.rows if row.constraints.viable)
    assert answer.max_viable == viable[-1]


def test_empty_window_is_unsatisfiable(sample_buyer: Buyer) -> None:
    answer = resolve(
        PriceUnknown(buyer=sample_buyer, min_price=2_000_000, max_price=2_100_000, step=10_000),
        AUGUST_2026,
    )

    assert isinstance(answer, Unsatisfiable)
    assert answer.reason == "No price in this range is viable."
    assert answer.caveat == AUGUST_2026.caveat


def test_deposit_needed_at_three_hundred_fifty_thousand() -> None:
    answer = resolve(
        DepositAtPrice(
            earnings=Earnings(base_salary=90_000, bonus=0, bonus_counted_percent=50),
            price=350_000,
        ),
        AUGUST_2026,
    )

    assert isinstance(answer, DepositAnswer)
    assert answer.stamp_duty == 2_500
    assert answer.fees == 2_500
    assert answer.loan == 332_500
    assert answer.cash_needed == 22_500


def test_income_needed_at_three_hundred_fifty_thousand() -> None:
    answer = resolve(
        IncomeAtPrice(
            funds=Funds(cash=40_000, lisa=10_000),
            price=350_000,
        ),
        AUGUST_2026,
    )

    assert isinstance(answer, IncomeAnswer)
    assert answer.loan == 305_000
    assert answer.assessed_income_needed == 67_778
