# tools/scraper - Agent Guide

Purpose: manually invoked live listing ingest into SQLite.
Layer: tool; may import concrete modules from `lhf.listings` and `lhf.db` (not barrels).
Commands: `uv run pytest tools/scraper/tests` and `uv run pyright tools/scraper`.
Conventions: `just scrape` is the only user entrypoint. It runs Rightmove then
OnTheMarket against the same SQLite file and the same `IngestWindow`. Product
ingest defaults live in `lhf.scraper.window` (`IngestWindow` / `DEFAULT_WINDOW`):
£350,000–£800,000 inclusive, min 2 bedrooms, detached/semi-detached/terraced/bungalow,
FREEHOLD. There is no `--source` flag. Each source replaces only its own rows via
`ListingRepository.replace_source`. `list_all` stays unfiltered.
Rightmove lives in `lhf.scraper.rightmove` and uses London BUY REGION 87490
plus every in-cap `find.html` page. Fetch with Playwright Chromium (lazy-start on
first `get()`). Split overflowing shards on price, then bedrooms, until each
`resultCount` is ≤ 1008. Sidecar `{database}.scrape-checkpoint.json`.
OnTheMarket lives in `lhf.scraper.onthemarket`. Fetch with stdlib urllib (Chrome 131
macOS UA; do not follow redirects; HTTP 303 is an empty-page sentinel). Path shards
only (`/for-sale/{n}-bed-{kind}/{location}/`); never `min-price`, `max-price`,
`min-bedrooms`, or `prop-types`. In-cap iff `totalResults` ≤ 1020. Sidecar
`{database}.onthemarket-scrape-checkpoint.json`. Do not import `lhf.scraper.rightmove.*`
from `onthemarket`. Do not add a shared protocol until two sources share real
behaviour. Override with `just scrape --min-price N --max-price N --min-bedrooms N`,
`--property-types csv`, `--tenure FREEHOLD|any`, and optional `--max-pages N`
(omit for all pages). `just scrape` forwards only the flags you pass, so omitted
window flags take `DEFAULT_WINDOW` from the CLI. `just scrape --resume` continues
a source that still has a sidecar when the window flags match. A source whose
sidecar is gone is skipped if no earlier source is still in progress, and started
fresh if an earlier source was interrupted before it ran. It errors only when both
sidecars are missing. Listings for a source are
replaced only when that source completes with at least one listing; an unusable
search page or a completed run with no cards leaves that source's rows untouched.
A fresh `just scrape` warns and discards leftover sidecars independently.
Parse HTML listing pages only — never call vendor `/api/*`. Keep parsing
deterministic and network access out of tests (recorded HTML fixtures; do not
launch a browser or use the network). After `uv sync --all-packages`, run
`uv run playwright install chromium` for Rightmove.
Detail payloads include Rightmove `termsOfUse` text claiming the embedded API is
for Rightmove only; that is an observation, not a permission grant.
Never: import the API app or create a background service.
