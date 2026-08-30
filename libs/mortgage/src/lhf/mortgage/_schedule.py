from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from lhf.mortgage.snapshot import LtvProduct, Snapshot


def stamp_duty(price: int, snapshot: Snapshot) -> int:
    bands = snapshot.ftb_bands if price <= snapshot.ftb_relief_cap else snapshot.standard_bands
    duty = Decimal(0)
    lower = 0
    for band in bands:
        if price <= lower:
            break
        upper = price if band.ceiling is None else band.ceiling
        slice_size = min(price, upper) - lower
        if slice_size > 0:
            duty += Decimal(slice_size) * band.rate
        if band.ceiling is None:
            break
        lower = band.ceiling
    return int(duty.to_integral_value(rounding=ROUND_HALF_UP))


def lisa_applied(lisa: int, price: int, snapshot: Snapshot) -> int:
    if price > snapshot.lisa_cap:
        return lisa * (100 - snapshot.lisa_penalty_percent) // 100
    return lisa


def snap_ltv(actual_ltv: Decimal, products: tuple[LtvProduct, ...]) -> LtvProduct | None:
    for product in products:
        if actual_ltv <= product.ceiling:
            return product
    return None


def monthly_repayment(loan: int, annual_rate: Decimal, term_years: int) -> int:
    if loan <= 0:
        return 0
    payments = term_years * 12
    monthly_rate = annual_rate / Decimal(12)
    if monthly_rate == 0:
        return int((Decimal(loan) / Decimal(payments)).to_integral_value(rounding=ROUND_HALF_UP))
    growth = (Decimal(1) + monthly_rate) ** payments
    payment = Decimal(loan) * monthly_rate * growth / (growth - Decimal(1))
    return int(payment.to_integral_value(rounding=ROUND_HALF_UP))
