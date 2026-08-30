# libs/mortgage - Agent Guide

Purpose: first-time-buyer mortgage viability (snapshot, evaluate, enquiry).
Layer: feature library beside `libs/listings`; never import apps, tools, `lhf.db`, or `lhf.listings`.
Public modules: `lhf.mortgage.snapshot`, `lhf.mortgage.buyer`, `lhf.mortgage.evaluate`,
`lhf.mortgage.enquiry` — import these directly; no barrel `api` module. `_schedule` stays
package-private.
Commands: `uv run pytest libs/mortgage/tests` and `uv run pyright libs/mortgage`.
Conventions: money is integer pounds; rates are `Decimal` fractions; frozen dataclasses;
`evaluate_at_price` is the canonical operation; `scan` only maps that over a grid.
Test fixtures use a fictional sample buyer, never a real operator's figures.
Never: rich, argparse, live rate fetches, or re-export barrels.
