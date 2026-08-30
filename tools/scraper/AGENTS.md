# tools/scraper - Agent Guide

Purpose: manually invoked live listing ingest into SQLite.
Layer: tool; may import concrete modules from `lhf.listings` and `lhf.db` (not barrels).
Commands: `uv run pytest tools/scraper/tests` and `uv run pyright tools/scraper`.
Conventions: `just scrape` is the only user entrypoint. `--source rightmove|zoopla`
selects the ingest package; omitted `--source` is Rightmove. Product ingest defaults
live in `lhf.scraper.window` (`IngestWindow` / `DEFAULT_WINDOW`): £350,000–£800,000
inclusive, min 2 bedrooms, detached/semi-detached/terraced/bungalow, FREEHOLD.
Rightmove lives in `lhf.scraper.rightmove` and uses London BUY REGION 87490
plus every in-cap search page. Zoopla lives in `lhf.scraper.zoopla` as a sibling
package (do not import `lhf.scraper.rightmove` from it). Zoopla search URLs are
`/for-sale/houses/london/` when `property_types` is set, otherwise
`/for-sale/property/london/`; never `q=`, `/search/`, or `/api/*`. Zoopla
`resultCount` is in-cap iff it is ≤ 1000 (`pn` 1–40, 25 cards/page); `pn` past
the last page is HTTP 404. Persist Zoopla to `listings_zoopla` via
`ListingRepository.replace_zoopla`; `replace_all` remains Rightmove-only.
Add a future source as a sibling package under `lhf.scraper`; do not add a
shared protocol until two sources share real behaviour. Override with
`just scrape --min-price N --max-price N --min-bedrooms N`,
`--property-types csv`, `--tenure FREEHOLD|any`, and optional `--max-pages N`
(omit for all pages). `just scrape` forwards only the flags you pass, so omitted
window flags take `DEFAULT_WINDOW` from the CLI. `just scrape --resume` continues
the sidecar `{database}.scrape-checkpoint.json` (Rightmove) or
`{database}.zoopla-scrape-checkpoint.json` (Zoopla) when the window flags match;
listings for that source are replaced only when a run completes with at least
one listing; an unusable search page or a completed run with no cards leaves
the database untouched. A fresh `just scrape` warns and discards a leftover
checkpoint. Fetch pages with Playwright, preferring system Chrome
(`channel="chrome"`) then bundled Chromium (lazy-start on first `get()`).
Split overflowing search shards on price, then bedrooms, until each
`resultCount` is in-cap; union unique listing ids. Parse search and detail HTML
only — never call vendor `/api/*`. Keep parsing deterministic and network
access out of tests (recorded HTML fixtures; do not launch a browser). After
`uv sync --all-packages`, run `uv run playwright install chromium`.
Detail payloads include Rightmove `termsOfUse` text claiming the embedded API is
for Rightmove only; that is an observation, not a permission grant.
Never: import the API app or create a background service.
