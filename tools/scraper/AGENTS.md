# tools/scraper - Agent Guide

Purpose: manually invoked live listing ingest into SQLite.
Layer: tool; may import concrete modules from `lhf.listings` and `lhf.db` (not barrels).
Commands: `uv run pytest tools/scraper/tests` and `uv run pyright tools/scraper`.
Conventions: `just scrape` is the only user entrypoint. Product ingest defaults live
in `lhf.scraper.window` (`IngestWindow` / `DEFAULT_WINDOW`): £350,000–£800,000
inclusive, min 2 bedrooms, detached/semi-detached/terraced/bungalow, FREEHOLD.
Rightmove lives in `lhf.scraper.rightmove` and uses London BUY REGION 87490
plus every in-cap search page. Add a future source as a sibling package under
`lhf.scraper`; do not add a shared protocol until two sources share real
behaviour. Override with `just scrape --min-price N --max-price N --min-bedrooms N`,
`--property-types csv`, `--tenure FREEHOLD|any`, and optional `--max-pages N`
(omit for all pages). `just scrape` forwards only the flags you pass, so omitted
window flags take `DEFAULT_WINDOW` from the CLI. `just scrape --resume` continues the
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
