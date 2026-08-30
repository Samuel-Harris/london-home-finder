from __future__ import annotations

import argparse
from collections.abc import Sequence
from dataclasses import replace
from decimal import Decimal, InvalidOperation
from typing import assert_never

from lhf.mortgage.buyer import Buyer, Earnings, Funds
from lhf.mortgage.enquiry import (
    Answer,
    DepositAnswer,
    DepositAtPrice,
    Enquiry,
    IncomeAnswer,
    IncomeAtPrice,
    MonthlyAnswer,
    MonthlyAtPrice,
    PriceTableAnswer,
    PriceUnknown,
    PriceUnknownCappedByMonthly,
    Unsatisfiable,
    resolve,
)
from lhf.mortgage.evaluate import PricePoint
from lhf.mortgage.snapshot import AUGUST_2026, Snapshot
from rich.console import Console
from rich.table import Table


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    arguments = parser.parse_args(argv)
    try:
        snapshot = _snapshot(arguments)
        enquiry = _enquiry(arguments)
        answer = resolve(enquiry, snapshot)
    except ValueError as exc:
        parser.error(str(exc))
    return _render(answer)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Estimate first-time-buyer mortgage viability from an August 2026 snapshot."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    price = subparsers.add_parser("price", help="scan candidate purchase prices")
    _add_earnings(price)
    _add_funds(price)
    _add_term(price)
    _add_overlays(price)
    price.add_argument("--monthly", type=int)
    price.add_argument("--min-price", type=int, default=100_000)
    price.add_argument("--max-price", type=int, default=1_500_000)
    price.add_argument("--step", type=int, default=10_000)

    monthly = subparsers.add_parser("monthly", help="monthly repayment at a known price")
    _add_earnings(monthly)
    _add_funds(monthly)
    _add_term(monthly)
    _add_overlays(monthly)
    monthly.add_argument("--price", type=int, required=True)

    deposit = subparsers.add_parser("deposit", help="cash needed at a known price")
    _add_earnings(deposit)
    _add_overlays(deposit)
    deposit.add_argument("--price", type=int, required=True)

    income = subparsers.add_parser("income", help="assessed income needed at a known price")
    _add_funds(income)
    _add_overlays(income)
    income.add_argument("--price", type=int, required=True)

    return parser


def _add_earnings(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--base-salary", type=int, required=True)
    parser.add_argument("--bonus", type=int, default=0)
    parser.add_argument("--bonus-counted-percent", type=int, default=50)


def _add_funds(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--cash", type=int, required=True)
    parser.add_argument("--lisa", type=int, default=0)


def _add_term(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--term", type=int, default=25)


def _add_overlays(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--income-multiple", type=_parse_decimal)
    parser.add_argument("--fixed-fees", type=int)


def _parse_decimal(value: str) -> Decimal:
    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise argparse.ArgumentTypeError(f"invalid decimal value: {value!r}") from exc


def _snapshot(arguments: argparse.Namespace) -> Snapshot:
    snapshot = AUGUST_2026
    if arguments.income_multiple is not None:
        snapshot = replace(snapshot, income_multiple=arguments.income_multiple)
    if arguments.fixed_fees is not None:
        snapshot = replace(snapshot, fixed_fees=arguments.fixed_fees)
    return snapshot


def _enquiry(arguments: argparse.Namespace) -> Enquiry:
    match arguments.command:
        case "price":
            buyer = _buyer(arguments)
            if arguments.monthly is None:
                return PriceUnknown(
                    buyer=buyer,
                    min_price=arguments.min_price,
                    max_price=arguments.max_price,
                    step=arguments.step,
                )
            return PriceUnknownCappedByMonthly(
                buyer=buyer,
                monthly=arguments.monthly,
                min_price=arguments.min_price,
                max_price=arguments.max_price,
                step=arguments.step,
            )
        case "monthly":
            return MonthlyAtPrice(buyer=_buyer(arguments), price=arguments.price)
        case "deposit":
            return DepositAtPrice(earnings=_earnings(arguments), price=arguments.price)
        case "income":
            return IncomeAtPrice(funds=_funds(arguments), price=arguments.price)
        case _:
            raise ValueError(f"unknown command: {arguments.command}")


def _buyer(arguments: argparse.Namespace) -> Buyer:
    return Buyer(earnings=_earnings(arguments), funds=_funds(arguments), term_years=arguments.term)


def _earnings(arguments: argparse.Namespace) -> Earnings:
    return Earnings(
        base_salary=arguments.base_salary,
        bonus=arguments.bonus,
        bonus_counted_percent=arguments.bonus_counted_percent,
    )


def _funds(arguments: argparse.Namespace) -> Funds:
    return Funds(cash=arguments.cash, lisa=arguments.lisa)


def _render(answer: Answer) -> int:
    console = Console()
    match answer:
        case Unsatisfiable():
            console.print(answer.reason)
            _print_caveat(console, answer.caveat)
            return 1
        case PriceTableAnswer():
            _print_table(console, answer)
        case MonthlyAnswer():
            _print_monthly(console, answer)
        case DepositAnswer():
            console.print(f"Cash needed: £{answer.cash_needed:,}")
            console.print(f"Price: £{answer.price:,}")
            console.print(f"Stamp duty: £{answer.stamp_duty:,}")
            console.print(f"Fees: £{answer.fees:,}")
            console.print(f"Loan: £{answer.loan:,}")
            _print_caveat(console, answer.caveat)
        case IncomeAnswer():
            console.print(f"Assessed income needed: £{answer.assessed_income_needed:,}")
            console.print(f"Price: £{answer.price:,}")
            console.print(f"Loan: £{answer.loan:,}")
            _print_caveat(console, answer.caveat)
        case _:
            assert_never(answer)
    return 0


def _print_table(console: Console, answer: PriceTableAnswer) -> None:
    table = Table(title="Mortgage viability")
    table.add_column("Price", justify="right")
    table.add_column("Stamp duty", justify="right")
    table.add_column("Deposit", justify="right")
    table.add_column("Loan", justify="right")
    table.add_column("LTV", justify="right")
    table.add_column("Monthly", justify="right")
    table.add_column("Status")
    for row in answer.rows:
        table.add_row(
            _pounds(row.price),
            _pounds(row.stamp_duty),
            _pounds(row.usable_deposit),
            _pounds(row.loan),
            _ltv(row),
            _monthly(row),
            _status(row, max_viable=answer.max_viable),
        )
    console.print(table)
    console.print(f"Highest viable price: {_pounds(answer.max_viable.price)}")
    _print_caveat(console, answer.caveat)


def _print_monthly(console: Console, answer: MonthlyAnswer) -> None:
    point = answer.point
    monthly = "n/a" if point.monthly is None else _pounds(point.monthly)
    console.print(f"Monthly repayment: {monthly}")
    console.print(f"Price: {_pounds(point.price)}")
    console.print(f"Loan: {_pounds(point.loan)}")
    console.print(f"Status: {_status(point)}")
    _print_caveat(console, answer.caveat)


def _print_caveat(console: Console, caveat: str) -> None:
    console.print(caveat)


def _pounds(value: int) -> str:
    return f"£{value:,}"


def _ltv(row: PricePoint) -> str:
    percent = (row.actual_ltv * Decimal(100)).quantize(Decimal("0.1"))
    return f"{percent}%"


def _monthly(row: PricePoint) -> str:
    if row.monthly is None:
        return "n/a"
    return _pounds(row.monthly)


def _status(row: PricePoint, max_viable: PricePoint | None = None) -> str:
    if row.constraints.viable:
        if (
            max_viable is not None
            and max_viable.monthly is not None
            and row.monthly is not None
            and row.monthly > max_viable.monthly
        ):
            return "over monthly"
        return "viable"
    binding = row.constraints.binding
    if binding is None:
        return "not viable"
    return binding
