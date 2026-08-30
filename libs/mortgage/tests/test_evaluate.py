from __future__ import annotations

from dataclasses import replace
from decimal import Decimal

import pytest
from lhf.mortgage.buyer import Buyer, Earnings, Funds
from lhf.mortgage.evaluate import PriceBounds, evaluate_at_price, scan
from lhf.mortgage.snapshot import AUGUST_2026, LtvProduct


def test_five_hundred_thousand_forward(golden_buyer: Buyer) -> None:
    point = evaluate_at_price(AUGUST_2026, golden_buyer, 500_000)

    assert point.lisa_applied == 12_000
    assert point.stamp_duty == 10_000
    assert point.fees == 2_500
    assert point.usable_deposit == 36_500
    assert point.loan == 463_500
    assert point.ltv_band == Decimal("0.95")
    assert point.rate == Decimal("0.056")
    assert point.monthly is not None
    assert abs(point.monthly - 2870) <= 20
    assert point.constraints.viable
    assert point.constraints.binding is None


def test_four_hundred_ten_thousand_forward(golden_buyer: Buyer) -> None:
    point = evaluate_at_price(AUGUST_2026, golden_buyer, 410_000)

    assert point.lisa_applied == 16_000
    assert point.stamp_duty == 5_500
    assert point.fees == 2_500
    assert point.usable_deposit == 45_000
    assert point.loan == 365_000
    assert point.ltv_band == Decimal("0.90")
    assert point.rate == Decimal("0.052")
    assert point.monthly is not None
    assert abs(point.monthly - 2200) <= 30
    assert point.constraints.viable


def test_scan_maps_evaluate_at_price(golden_buyer: Buyer) -> None:
    bounds = PriceBounds(min_price=400_000, max_price=420_000)
    rows = scan(golden_buyer, AUGUST_2026, bounds, 10_000)

    assert tuple(row.price for row in rows) == (400_000, 410_000, 420_000)
    for row in rows:
        assert row == evaluate_at_price(AUGUST_2026, golden_buyer, row.price)


def test_scan_includes_unaligned_max_price(golden_buyer: Buyer) -> None:
    bounds = PriceBounds(min_price=400_000, max_price=415_000)
    rows = scan(golden_buyer, AUGUST_2026, bounds, 10_000)

    assert tuple(row.price for row in rows) == (400_000, 410_000, 415_000)


def test_deposit_binds_before_product() -> None:
    buyer = Buyer(
        earnings=Earnings(base_salary=115_000, bonus=0, bonus_counted_percent=50),
        funds=Funds(cash=0, lisa=0),
        term_years=25,
    )
    point = evaluate_at_price(AUGUST_2026, buyer, 500_000)

    assert point.usable_deposit < 0
    assert point.constraints.viable is False
    assert point.constraints.binding == "deposit"


def test_cash_purchase_clamps_loan_at_zero() -> None:
    buyer = Buyer(
        earnings=Earnings(base_salary=115_000, bonus=0, bonus_counted_percent=50),
        funds=Funds(cash=1_000_000, lisa=0),
        term_years=25,
    )
    point = evaluate_at_price(AUGUST_2026, buyer, 10_000)

    assert point.loan == 0
    assert point.actual_ltv == 0
    assert point.monthly == 0
    assert point.constraints.viable
    assert point.constraints.binding is None


def test_snapshot_rejects_non_increasing_ltv_ceilings() -> None:
    with pytest.raises(ValueError, match="strictly increasing"):
        replace(
            AUGUST_2026,
            ltv_products=(
                LtvProduct(ceiling=Decimal("0.90"), annual_rate=Decimal("0.05")),
                LtvProduct(ceiling=Decimal("0.80"), annual_rate=Decimal("0.06")),
            ),
        )
