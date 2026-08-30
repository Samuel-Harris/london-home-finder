# Worked example: Rightmove

Lessons from this repository's Rightmove ingest. Procedure stays in `SKILL.md`. Copy keys only after you have saved live HTML for the site you are actually scraping.

## Files to read (do not invent a parallel scraper)

```text
tools/scraper/AGENTS.md
tools/scraper/src/lhf/scraper/window.py              DEFAULT_WINDOW
tools/scraper/src/lhf/scraper/cli.py
tools/scraper/src/lhf/scraper/rightmove/http.py      Playwright Fetcher
tools/scraper/src/lhf/scraper/rightmove/search.py    __NEXT_DATA__ → SearchCard
tools/scraper/src/lhf/scraper/rightmove/detail.py    packed __PAGE_MODEL
tools/scraper/src/lhf/scraper/rightmove/json_values.py
tools/scraper/src/lhf/scraper/rightmove/map_listing.py
tools/scraper/src/lhf/scraper/rightmove/shards.py
tools/scraper/src/lhf/scraper/rightmove/scrape.py
tools/scraper/src/lhf/scraper/rightmove/checkpoint.py
tools/scraper/tests/rightmove/fixtures/
```

## Embeds

Search `find.html` is Next.js `__NEXT_DATA__` → `props.pageProps.searchResults.properties` plus `resultCount` (int or `"1,008"`).

Detail `/properties/{id}` is packed `window.__PAGE_MODEL = { data: "<json array string>" }`. Slot 0 is `{key: index}`. Other slots are values or nested index refs. Cycle-guard the resolver. See `_extract_page_model` and `_unpack` in `detail.py`.

## Pagination cap

Page size 24. Last working `index` is 984 (42 pages). About 1008 cards. `index=1008` is empty. A shard is complete iff `resultCount ≤ 1008`. Unfiltered London BUY is not the market. It is the highest-price slice plus featured cards.

Query params that change `resultCount` on `find.html`: `locationIdentifier`, `channel`, `transactionType`, `minPrice`, `maxPrice`, `minBedrooms`, `maxBedrooms`, `propertyTypes`, `tenureTypes`, `index`.

Split price `[min, mid]` / `[mid+1, max]` first. When `min_price == max_price`, split bedrooms. Fail if one pound and one bedroom count still overflow.

Featured cards leak other price bands and can duplicate ids. Dedupe by listing id. Drop when asking price is known and outside the **window**. Keep POA.

## Fetch

curl plus Chrome UA worked for research. Live ingest needed Playwright after Fastly 403 (error 54113). Prefer `channel="chrome"`, then bundled Chromium. `uv run playwright install chromium`.

`wait_until="domcontentloaded"` is enough when the payload is in the first HTML. `page.goto` does not throw on HTTP 403. After `chrome-error://chromewebdata/`, close the page and `new_page()`. Do not retry `goto` on the poisoned tab.

## Map gotchas

- `yearsRemainingOnLease` of `0` on freehold is not zero years left. Store lease years only for LEASEHOLD / SHARE_OF_FREEHOLD and only if `> 0`.
- Live sizings use `maximumSize` / `minimumSize`. Older fixtures used `maximum` / `minimum`. Prefer live keys, then fall back.
- Search `displaySize` is often `"1,234 sq ft"`. Prefer detail `sizings[]`.
- Store the property URL, not the `find.html` search URL.
- `termsOfUse` in the detail payload claims the embedded API is Rightmove-only. Observation only. This project fetches `find.html` and `/properties/{id}` only.

## Persist in this repo today

Rightmove still writes the shared `listings` table via `ListingRepository.replace_all`, which deletes every row. The skill persist rule is one table per source. Do not add Zoopla (or any second source) onto `listings`. Split first.

Default window lives in `lhf.scraper.window.DEFAULT_WINDOW`. Phase D runs `just scrape` with no window-flag overrides (omitted flags take `DEFAULT_WINDOW`).
