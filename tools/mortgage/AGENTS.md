# tools/mortgage - Agent Guide

Purpose: operator CLI for first-time-buyer mortgage viability.
Layer: tool; may import concrete modules from `lhf.mortgage` (not barrels).
Public modules: `lhf.mortgage_cli.cli`.
Commands: `uv run pytest tools/mortgage/tests` and `uv run pyright tools/mortgage`.
Conventions: `just mortgage` is the user entrypoint (`uv run lhf-mortgage`). Subcommands
name the unknown (`price`, `monthly`, `deposit`, `income`). Always print the snapshot
caveat. Domain maths stay in `lhf.mortgage`. When the user asks what they can afford,
run the CLI only after this request states every input that subcommand needs. Confirm
gaps before running. Do not fill them from earlier chat, fixtures, or CLI defaults.
`price` needs `--base-salary` and `--cash`, plus `--monthly` when they named a
repayment cap, and `--bonus` / `--lisa` / `--term` when those apply. `monthly` needs
`--base-salary`, `--cash`, and `--price`. `deposit` needs `--base-salary` and
`--price`. `income` needs `--cash` and `--price`.
Never: import apps, listings, or `lhf.mortgage._schedule`. Never invent salary, bonus,
LISA, cash, price, term, or a monthly cap. Never write a real operator's income, bonus,
cash, or LISA into the repository; tests use a fictional sample buyer.
