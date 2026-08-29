# tools/scraper - Agent Guide

Purpose: manually invoked live Rightmove HTML ingest into SQLite.
Layer: tool; may import concrete modules from `lhf.listings` and `lhf.db` (not barrels).
Commands: `uv run pytest tools/scraper/tests` and `uv run pyright tools/scraper`.
Conventions: `just scrape` is the only user entrypoint. Defaults are London BUY
REGION 87490, £350,000–£800,000 inclusive, min 2 bedrooms, detached/
semi-detached/terraced/bungalow, FREEHOLD, and every in-cap search page.
Override with `just scrape --min-price N --max-price N --min-bedrooms N`,
`--property-types csv`, `--tenure FREEHOLD|any`, and optional `--max-pages N`
(omit for all pages). `just scrape --resume` continues the
sidecar `{database}.scrape-checkpoint.json` when the window flags match;
listings are replaced only when a run completes with at least one listing;
an unusable search page or a completed run with no cards leaves the database
untouched. A fresh `just scrape` warns and discards a leftover checkpoint.
Fetch pages with Playwright Chromium (lazy-start on first `get()`). Split
overflowing `find.html` shards on price, then bedrooms, until each
`resultCount` is ≤ 1008; union unique listing ids.
Parse `find.html` and
`/properties/{id}` HTML only — never call Rightmove `/api/*`. Keep parsing
deterministic and network access out of tests (recorded HTML fixtures; do not
launch a browser). After `uv sync --all-packages`, run
`uv run playwright install chromium`.
Detail payloads include Rightmove `termsOfUse` text claiming the embedded API is
for Rightmove only; that is an observation, not a permission grant.
Never: import the API app or create a background service.
