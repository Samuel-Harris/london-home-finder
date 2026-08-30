from __future__ import annotations

import pytest
from lhf.mortgage.buyer import Buyer, Earnings, Funds


@pytest.fixture
def sample_buyer() -> Buyer:
    return Buyer(
        earnings=Earnings(base_salary=90_000, bonus=0, bonus_counted_percent=50),
        funds=Funds(cash=40_000, lisa=10_000),
        term_years=25,
    )
