from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True, kw_only=True)
class StampDutyBand:
    ceiling: int | None
    rate: Decimal

    def __post_init__(self) -> None:
        if self.ceiling is not None and self.ceiling <= 0:
            raise ValueError("stamp duty band ceiling must be positive")
        if self.rate < 0:
            raise ValueError("stamp duty rate must not be negative")


@dataclass(frozen=True, slots=True, kw_only=True)
class LtvProduct:
    ceiling: Decimal
    annual_rate: Decimal

    def __post_init__(self) -> None:
        if self.ceiling <= 0:
            raise ValueError("LTV ceiling must be positive")
        if self.annual_rate < 0:
            raise ValueError("LTV annual rate must not be negative")


@dataclass(frozen=True, slots=True, kw_only=True)
class Snapshot:
    income_multiple: Decimal
    lisa_cap: int
    lisa_penalty_percent: int
    fixed_fees: int
    ftb_relief_cap: int
    ftb_bands: tuple[StampDutyBand, ...]
    standard_bands: tuple[StampDutyBand, ...]
    ltv_products: tuple[LtvProduct, ...]
    caveat: str

    def __post_init__(self) -> None:
        if self.income_multiple <= 0:
            raise ValueError("income_multiple must be positive")
        if self.lisa_cap <= 0:
            raise ValueError("lisa_cap must be positive")
        if not 0 <= self.lisa_penalty_percent <= 100:
            raise ValueError("lisa_penalty_percent must be between 0 and 100")
        if self.fixed_fees < 0:
            raise ValueError("fixed_fees must not be negative")
        if self.ftb_relief_cap <= 0:
            raise ValueError("ftb_relief_cap must be positive")
        if not self.ftb_bands:
            raise ValueError("ftb_bands must not be empty")
        if not self.standard_bands:
            raise ValueError("standard_bands must not be empty")
        if not self.ltv_products:
            raise ValueError("ltv_products must not be empty")
        ceilings = tuple(product.ceiling for product in self.ltv_products)
        if any(earlier >= later for earlier, later in zip(ceilings, ceilings[1:], strict=False)):
            raise ValueError("LTV ceilings must be strictly increasing")
        rates = tuple(product.annual_rate for product in self.ltv_products)
        if any(earlier > later for earlier, later in zip(rates, rates[1:], strict=False)):
            raise ValueError("LTV annual rates must be non-decreasing")


AUGUST_2026 = Snapshot(
    income_multiple=Decimal("4.5"),
    lisa_cap=450_000,
    lisa_penalty_percent=25,
    fixed_fees=2_500,
    ftb_relief_cap=500_000,
    ftb_bands=(
        StampDutyBand(ceiling=300_000, rate=Decimal("0")),
        StampDutyBand(ceiling=500_000, rate=Decimal("0.05")),
    ),
    standard_bands=(
        StampDutyBand(ceiling=125_000, rate=Decimal("0")),
        StampDutyBand(ceiling=250_000, rate=Decimal("0.02")),
        StampDutyBand(ceiling=925_000, rate=Decimal("0.05")),
        StampDutyBand(ceiling=1_500_000, rate=Decimal("0.10")),
        StampDutyBand(ceiling=None, rate=Decimal("0.12")),
    ),
    ltv_products=(
        LtvProduct(ceiling=Decimal("0.60"), annual_rate=Decimal("0.046")),
        LtvProduct(ceiling=Decimal("0.75"), annual_rate=Decimal("0.049")),
        LtvProduct(ceiling=Decimal("0.80"), annual_rate=Decimal("0.051")),
        LtvProduct(ceiling=Decimal("0.85"), annual_rate=Decimal("0.051")),
        LtvProduct(ceiling=Decimal("0.90"), annual_rate=Decimal("0.052")),
        LtvProduct(ceiling=Decimal("0.95"), annual_rate=Decimal("0.056")),
    ),
    caveat=("This is a planning model using an August 2026 snapshot. It is not financial advice."),
)
