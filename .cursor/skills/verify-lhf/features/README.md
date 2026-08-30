# London Home Finder verification map

This directory is the maintained source for verifying user-facing behaviour. Read this index before driving the app, then use the matching feature file as the recipe.

## Baseline preconditions

- Launch with `uv run python .cursor/skills/verify-lhf/scripts/control_lhf.py launch`.
- Drive only `http://127.0.0.1:18781` (web) and `http://127.0.0.1:18780` (API).
- Run `uv run python .cursor/skills/verify-lhf/scripts/control_lhf.py doctor` and require `ok: true`.
- Never drive an instance that was not started by this verification run, including `just dev-api` on port 8000 and `just dev-web` on port 3000.
- Write proof under the `evidence_dir` printed by launch. Cleanup must leave those files in place.

## Driving conventions

- Start every recipe from the baseline state unless its preconditions say otherwise.
- Prefer ARIA roles and accessible names over CSS selectors or DOM position.
- Treat every command as literal. Keep quoted names and flags unchanged.
- Run browser actions through `control_lhf.py browser`.
- Run API actions through `control_lhf.py http get`.
- `seed-listing` is fixture setup for the listings API, not a user entry point.
- Do not remove proof artefacts during cleanup.

## Proof and skip reporting

- Capture the user action and the resulting state, not only the final screen.
- UI proof includes an ARIA snapshot and a screenshot that shows the product heading and the isolated API URL.
- HTTP proof includes the command, status code, and response body.
- Record the feature ID and entry point used with every artefact.
- Report an unreachable path with the attempted command and the unmet precondition.
- Do not report a skipped entry point as verified through a different path.
- `just scrape` is out of scope: it fetches live Rightmove pages and writes the shared (or passed) SQLite file.

## Feature entry contract

Each feature file starts with an H1 title and one paragraph describing the user-visible behaviour. It then uses exactly four H2 sections in this order.

1. `Sub-features` lists short IDs with one line for each behaviour.
2. `How to get to it (user POV)` lists every user entry point.
3. `Driving it with control_lhf` starts with `Preconditions:` and uses labelled bullets that pair each user action with an exact command and observable result.
4. `Gotchas` lists traps that can waste or invalidate a verification run.

Keep implementation details out of the map. Name only user paths, stable handles, required state, commands, and observable proof.

## Features

- [Home workspace](./home-workspace.md) covers the Next.js landing page identity and the displayed API connection.
- [API health](./api-health.md) covers `GET /health`.
- [List listings](./list-listings.md) covers `GET /listings` for an empty database and after seeding one fixture listing.
