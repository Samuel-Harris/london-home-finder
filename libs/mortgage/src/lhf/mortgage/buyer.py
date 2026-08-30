from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True, kw_only=True)
class Earnings:
    base_salary: int
    bonus: int
    bonus_counted_percent: int

    def __post_init__(self) -> None:
        if self.base_salary <= 0:
            raise ValueError("base_salary must be positive")
        if self.bonus < 0:
            raise ValueError("bonus must not be negative")
        if not 0 <= self.bonus_counted_percent <= 100:
            raise ValueError("bonus_counted_percent must be between 0 and 100")

    @property
    def assessed_income(self) -> int:
        return self.base_salary + self.bonus * self.bonus_counted_percent // 100


@dataclass(frozen=True, slots=True, kw_only=True)
class Funds:
    cash: int
    lisa: int

    def __post_init__(self) -> None:
        if self.cash < 0:
            raise ValueError("cash must not be negative")
        if self.lisa < 0:
            raise ValueError("lisa must not be negative")


@dataclass(frozen=True, slots=True, kw_only=True)
class Buyer:
    earnings: Earnings
    funds: Funds
    term_years: int

    def __post_init__(self) -> None:
        if self.term_years < 1:
            raise ValueError("term_years must be at least 1")
