from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import assert_never

from lhf.mortgage.buyer import Buyer, Earnings, Funds
from lhf.mortgage.evaluate import (
    PriceBounds,
    PricePoint,
    evaluate_at_price,
    financing_at_price,
    income_needed,
    max_loan,
    purchase_costs,
    scan,
)
from lhf.mortgage.snapshot import Snapshot


@dataclass(frozen=True, slots=True, kw_only=True)
class PriceUnknown:
    buyer: Buyer
    min_price: int = 100_000
    max_price: int = 1_500_000
    step: int = 10_000

    def __post_init__(self) -> None:
        _require_price_window(self.min_price, self.max_price, self.step)


@dataclass(frozen=True, slots=True, kw_only=True)
class PriceUnknownCappedByMonthly:
    buyer: Buyer
    monthly: int
    min_price: int = 100_000
    max_price: int = 1_500_000
    step: int = 10_000

    def __post_init__(self) -> None:
        if self.monthly < 0:
            raise ValueError("monthly must not be negative")
        _require_price_window(self.min_price, self.max_price, self.step)


@dataclass(frozen=True, slots=True, kw_only=True)
class MonthlyAtPrice:
    buyer: Buyer
    price: int

    def __post_init__(self) -> None:
        if self.price <= 0:
            raise ValueError("price must be positive")


@dataclass(frozen=True, slots=True, kw_only=True)
class DepositAtPrice:
    earnings: Earnings
    price: int

    def __post_init__(self) -> None:
        if self.price <= 0:
            raise ValueError("price must be positive")


@dataclass(frozen=True, slots=True, kw_only=True)
class IncomeAtPrice:
    funds: Funds
    price: int

    def __post_init__(self) -> None:
        if self.price <= 0:
            raise ValueError("price must be positive")


type Enquiry = (
    PriceUnknown | PriceUnknownCappedByMonthly | MonthlyAtPrice | DepositAtPrice | IncomeAtPrice
)


@dataclass(frozen=True, slots=True, kw_only=True)
class PriceTableAnswer:
    rows: tuple[PricePoint, ...]
    max_viable: PricePoint
    caveat: str


@dataclass(frozen=True, slots=True, kw_only=True)
class MonthlyAnswer:
    point: PricePoint
    caveat: str


@dataclass(frozen=True, slots=True, kw_only=True)
class DepositAnswer:
    cash_needed: int
    price: int
    stamp_duty: int
    fees: int
    loan: int
    caveat: str


@dataclass(frozen=True, slots=True, kw_only=True)
class IncomeAnswer:
    assessed_income_needed: int
    price: int
    loan: int
    caveat: str


@dataclass(frozen=True, slots=True, kw_only=True)
class Unsatisfiable:
    reason: str
    caveat: str


type Answer = PriceTableAnswer | MonthlyAnswer | DepositAnswer | IncomeAnswer | Unsatisfiable


def resolve(enquiry: Enquiry, snapshot: Snapshot) -> Answer:
    match enquiry:
        case PriceUnknown():
            return _resolve_price_unknown(enquiry, snapshot)
        case PriceUnknownCappedByMonthly():
            return _resolve_price_unknown_capped(enquiry, snapshot)
        case MonthlyAtPrice():
            return MonthlyAnswer(
                point=evaluate_at_price(snapshot, enquiry.buyer, enquiry.price),
                caveat=snapshot.caveat,
            )
        case DepositAtPrice():
            return _resolve_deposit(enquiry, snapshot)
        case IncomeAtPrice():
            return _resolve_income(enquiry, snapshot)
        case _:
            assert_never(enquiry)


def _resolve_price_unknown(enquiry: PriceUnknown, snapshot: Snapshot) -> Answer:
    return _resolve_price_scan(
        enquiry.buyer,
        snapshot,
        enquiry.min_price,
        enquiry.max_price,
        enquiry.step,
        _is_viable,
        "No price in this range is viable.",
    )


def _resolve_price_unknown_capped(
    enquiry: PriceUnknownCappedByMonthly, snapshot: Snapshot
) -> Answer:
    return _resolve_price_scan(
        enquiry.buyer,
        snapshot,
        enquiry.min_price,
        enquiry.max_price,
        enquiry.step,
        lambda row: _under_monthly(row, enquiry.monthly),
        "No price in this range is viable with a monthly repayment at or below the cap.",
    )


def _resolve_price_scan(
    buyer: Buyer,
    snapshot: Snapshot,
    min_price: int,
    max_price: int,
    step: int,
    matches: Callable[[PricePoint], bool],
    unsatisfiable_reason: str,
) -> Answer:
    rows = scan(
        buyer,
        snapshot,
        PriceBounds(min_price=min_price, max_price=max_price),
        step,
    )
    last_coarse = _last_matching(rows, matches)
    if last_coarse is None:
        return Unsatisfiable(reason=unsatisfiable_reason, caveat=snapshot.caveat)
    following = _following_price(rows, last_coarse)
    max_viable = last_coarse
    if following is not None:
        max_viable = _densify(buyer, snapshot, last_coarse, following, matches)
    return PriceTableAnswer(
        rows=_rows_including(rows, max_viable),
        max_viable=max_viable,
        caveat=snapshot.caveat,
    )


def _resolve_deposit(enquiry: DepositAtPrice, snapshot: Snapshot) -> DepositAnswer:
    duty, fees = purchase_costs(snapshot, enquiry.price)
    loan = max_loan(enquiry.earnings.assessed_income, enquiry.price, snapshot)
    min_usable = enquiry.price - loan
    cash_needed = max(0, min_usable + duty + fees)
    return DepositAnswer(
        cash_needed=cash_needed,
        price=enquiry.price,
        stamp_duty=duty,
        fees=fees,
        loan=loan,
        caveat=snapshot.caveat,
    )


def _resolve_income(enquiry: IncomeAtPrice, snapshot: Snapshot) -> IncomeAnswer | Unsatisfiable:
    financing = financing_at_price(snapshot, enquiry.funds, enquiry.price)
    if financing.usable_deposit < 0:
        return Unsatisfiable(
            reason="These funds cannot cover the deposit, stamp duty, and fees at this price.",
            caveat=snapshot.caveat,
        )
    if financing.product is None:
        ceiling_percent = int(snapshot.ltv_products[-1].ceiling * 100)
        return Unsatisfiable(
            reason=f"The loan-to-value at this price is above {ceiling_percent} percent.",
            caveat=snapshot.caveat,
        )
    return IncomeAnswer(
        assessed_income_needed=income_needed(financing.loan, snapshot),
        price=enquiry.price,
        loan=financing.loan,
        caveat=snapshot.caveat,
    )


def _require_price_window(min_price: int, max_price: int, step: int) -> None:
    if min_price <= 0:
        raise ValueError("min_price must be positive")
    if max_price < min_price:
        raise ValueError("max_price must be at least min_price")
    if step < 1:
        raise ValueError("step must be at least 1")


def _is_viable(row: PricePoint) -> bool:
    return row.constraints.viable


def _under_monthly(row: PricePoint, cap: int) -> bool:
    return row.constraints.viable and row.monthly is not None and row.monthly <= cap


def _last_matching(
    rows: tuple[PricePoint, ...], matches: Callable[[PricePoint], bool]
) -> PricePoint | None:
    matched = tuple(row for row in rows if matches(row))
    return matched[-1] if matched else None


def _following_price(rows: tuple[PricePoint, ...], current: PricePoint) -> int | None:
    index = rows.index(current)
    if index + 1 >= len(rows):
        return None
    return rows[index + 1].price


def _densify(
    buyer: Buyer,
    snapshot: Snapshot,
    lower: PricePoint,
    upper_price: int,
    matches: Callable[[PricePoint], bool],
) -> PricePoint:
    best = lower
    for price in range(lower.price + 1, upper_price):
        point = evaluate_at_price(snapshot, buyer, price)
        if matches(point):
            best = point
    return best


def _rows_including(
    rows: tuple[PricePoint, ...], extra: PricePoint
) -> tuple[PricePoint, ...]:
    if any(row.price == extra.price for row in rows):
        return rows
    return tuple(sorted((*rows, extra), key=lambda row: row.price))
