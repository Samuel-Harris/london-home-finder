from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_CEILING, ROUND_DOWN, Decimal
from typing import Literal

from lhf.mortgage._schedule import lisa_applied, monthly_repayment, snap_ltv, stamp_duty
from lhf.mortgage.buyer import Buyer, Funds
from lhf.mortgage.snapshot import LtvProduct, Snapshot

type BindingConstraint = Literal["deposit", "product", "income"]


@dataclass(frozen=True, slots=True, kw_only=True)
class Constraints:
    viable: bool
    binding: BindingConstraint | None

    def __post_init__(self) -> None:
        if self.viable and self.binding is not None:
            raise ValueError("viable price points must not name a binding constraint")
        if not self.viable and self.binding is None:
            raise ValueError("non-viable price points must name a binding constraint")


@dataclass(frozen=True, slots=True, kw_only=True)
class Financing:
    price: int
    stamp_duty: int
    fees: int
    lisa_applied: int
    usable_deposit: int
    loan: int
    actual_ltv: Decimal
    product: LtvProduct | None


@dataclass(frozen=True, slots=True, kw_only=True)
class PricePoint:
    price: int
    stamp_duty: int
    fees: int
    lisa_applied: int
    usable_deposit: int
    loan: int
    actual_ltv: Decimal
    ltv_band: Decimal | None
    rate: Decimal | None
    monthly: int | None
    income_multiple: Decimal
    constraints: Constraints


@dataclass(frozen=True, slots=True, kw_only=True)
class PriceBounds:
    min_price: int
    max_price: int

    def __post_init__(self) -> None:
        if self.min_price <= 0:
            raise ValueError("min_price must be positive")
        if self.max_price < self.min_price:
            raise ValueError("max_price must be at least min_price")


def financing_at_price(snapshot: Snapshot, funds: Funds, price: int) -> Financing:
    if price <= 0:
        raise ValueError("price must be positive")
    duty = stamp_duty(price, snapshot)
    lisa = lisa_applied(funds.lisa, price, snapshot)
    usable_deposit = funds.cash + lisa - duty - snapshot.fixed_fees
    loan = max(0, price - usable_deposit)
    actual_ltv = Decimal(loan) / Decimal(price)
    return Financing(
        price=price,
        stamp_duty=duty,
        fees=snapshot.fixed_fees,
        lisa_applied=lisa,
        usable_deposit=usable_deposit,
        loan=loan,
        actual_ltv=actual_ltv,
        product=snap_ltv(actual_ltv, snapshot.ltv_products),
    )


def purchase_costs(snapshot: Snapshot, price: int) -> tuple[int, int]:
    if price <= 0:
        raise ValueError("price must be positive")
    return stamp_duty(price, snapshot), snapshot.fixed_fees


def income_loan_cap(assessed_income: int, snapshot: Snapshot) -> int:
    return int(
        (Decimal(assessed_income) * snapshot.income_multiple).to_integral_value(rounding=ROUND_DOWN)
    )


def income_needed(loan: int, snapshot: Snapshot) -> int:
    if loan <= 0:
        return 0
    return int((Decimal(loan) / snapshot.income_multiple).to_integral_value(rounding=ROUND_CEILING))


def max_loan(assessed_income: int, price: int, snapshot: Snapshot) -> int:
    ltv_cap = int(
        (Decimal(price) * snapshot.ltv_products[-1].ceiling).to_integral_value(rounding=ROUND_DOWN)
    )
    return max(0, min(income_loan_cap(assessed_income, snapshot), ltv_cap))


def evaluate_at_price(snapshot: Snapshot, buyer: Buyer, price: int) -> PricePoint:
    financing = financing_at_price(snapshot, buyer.funds, price)
    product = financing.product
    monthly = (
        None
        if product is None
        else monthly_repayment(financing.loan, product.annual_rate, buyer.term_years)
    )
    assessed = buyer.earnings.assessed_income
    cap = income_loan_cap(assessed, snapshot)
    deposit_clears = financing.usable_deposit >= 0
    product_clears = product is not None
    income_clears = financing.loan <= cap
    viable = deposit_clears and product_clears and income_clears
    binding: BindingConstraint | None
    if viable:
        binding = None
    elif not deposit_clears:
        binding = "deposit"
    elif not product_clears:
        binding = "product"
    else:
        binding = "income"
    return PricePoint(
        price=price,
        stamp_duty=financing.stamp_duty,
        fees=financing.fees,
        lisa_applied=financing.lisa_applied,
        usable_deposit=financing.usable_deposit,
        loan=financing.loan,
        actual_ltv=financing.actual_ltv,
        ltv_band=None if product is None else product.ceiling,
        rate=None if product is None else product.annual_rate,
        monthly=monthly,
        income_multiple=Decimal(financing.loan) / Decimal(assessed),
        constraints=Constraints(viable=viable, binding=binding),
    )


def scan(
    buyer: Buyer, snapshot: Snapshot, bounds: PriceBounds, step: int
) -> tuple[PricePoint, ...]:
    if step < 1:
        raise ValueError("step must be at least 1")
    return tuple(
        evaluate_at_price(snapshot, buyer, price)
        for price in _price_grid(bounds.min_price, bounds.max_price, step)
    )


def _price_grid(min_price: int, max_price: int, step: int) -> tuple[int, ...]:
    prices = list(range(min_price, max_price + 1, step))
    if prices[-1] != max_price:
        prices.append(max_price)
    return tuple(prices)
