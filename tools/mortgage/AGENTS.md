# tools/mortgage - Agent Guide

Purpose: operator CLI for first-time-buyer mortgage viability.
Layer: tool; may import concrete modules from `lhf.mortgage` (not barrels).
Public modules: `lhf.mortgage_cli.cli`.
Commands: `uv run pytest tools/mortgage/tests` and `uv run pyright tools/mortgage`.
Conventions: `just mortgage` is the user entrypoint (`uv run lhf-mortgage`). Subcommands
name the unknown (`price`, `monthly`, `deposit`, `income`). Always print the snapshot
caveat. Domain maths stay in `lhf.mortgage`.
Never: import apps, listings, or `lhf.mortgage._schedule`.
