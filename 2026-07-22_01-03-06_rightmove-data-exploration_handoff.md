# Handoff: Rightmove data exploration & field interest interview

## 1. Session Overview

- **Date/Time**: 2026-07-22_01-03-06
- **Primary Objective**: Explore what property metadata can be scraped from Rightmove (London buy search + detail pages), identify technical scraping issues, and (via deep interview) pin down which fields the user cares about for a London home-finder tool — **research only, no implementation**.
- **Current Status**: Research and interview **complete**. Spec crystallised. No scraper code written. Ready for a future session to decide whether/how to build ingestion (separate decision).

## 2. Context Summary

**Project:** `london-home-finder` monorepo — personal tool to help find a house to buy in London.

**Repo state (brownfield):** Fixture-only ingestion exists; no live Rightmove scraper.
- Scraper CLI: `import-fixture` → `ListingDraft` → SQLite upsert
- Domain `Listing`: `source`, `external_id`, `title`, `asking_price_gbp`, `postcode`, `url`, `floor_area_sqm`
- API: `GET /listings`; web app does not yet render listings

**Interview outcomes (passed at 12% ambiguity):**
- Goal of *this* work: inventory available data + technical scrape issues (not build).
- User interest set = **core economics**: price, beds, location/postcode, size when present, tenure/lease years, service charge/ground rent when present.
- Scope of data sources: **search results + detail pages**.
- Legal/ToS: observed and noted; user chose **technical-only** evaluation for this exploration (defer legal decision).

**Key technical findings:**
- Search embeds clean JSON in `__NEXT_DATA__` → `props.pageProps.searchResults.properties`.
- Detail embeds packed `window.__PAGE_MODEL = { data: "<json array string>" }` requiring index-graph unpack.
- Pagination hard-caps at **42 pages / index 984 / ~1,008 listings** per search, even when `resultCount` is ~60k.
- Price (and beds/location) sharding can cover the market **if** each shard’s `resultCount ≤ ~1008`; mid-market £25k bands still overflow — need finer/adaptive splits + dedupe by `id`.
- Core economics fields are often **null** on detail pages (especially ground rent; service charge frequently missing on leaseholds).

## 3. File Locations & Changes

```text
.cursor/artefacts/interviews/2026-07-22_00-52-54_rightmove-data-interest_interview.md
  - Crystallised deep-interview spec (goal, constraints, field mapping, scrape issues, Q&A)

.cursor/artefacts/handoffs/2026-07-22_01-03-06_rightmove-data-exploration_handoff.md
  - This handoff

No application/source code was modified. No commits.
```

**Ephemeral local artefacts (not in repo; may still exist on disk):**
- `/tmp/rm-find.html` — saved London search HTML
- `/tmp/rm-detail.html` — sample detail HTML (`/properties/88696923`)
- `/tmp/rm-detail-unpacked.json` — unpacked `__PAGE_MODEL` for that listing
- Uploaded copy: `~/.cursor/projects/.../uploads/find-0.html` (markdown/accessibility capture; less useful than live `__NEXT_DATA__`)

**Key existing code (unchanged, for future build context):**
- `tools/scraper/src/lhf_scraper/cli.py` — CLI entry (`import-fixture` only)
- `tools/scraper/src/lhf_scraper/fixture.py` — JSON → `ListingDraft`
- `libs/backend/src/lhf_backend/_listing.py` — domain model
- `libs/backend/src/lhf_backend/api.py` — public backend surface
- `apps/api/src/lhf_api/app.py` — `GET /listings`
- `tools/scraper/AGENTS.md` — scraper may import only `lhf_backend.api`; keep parsing deterministic; no network in tests

## 4. Completed Tasks

- [x] Fetched live Rightmove London BUY search; extracted search property schema from `__NEXT_DATA__`
- [x] Fetched sample detail page; reverse-engineered packed `__PAGE_MODEL` unpack
- [x] Mapped core-economics buyer fields → Rightmove keys (search + detail)
- [x] Documented technical scrape issues (cap, dual formats, sparsity, volume, noise, ToS text)
- [x] Verified pagination: pages exist but stop at ~1008; `index=1008` → “couldn’t find” page
- [x] Verified price sharding: `minPrice`/`maxPrice` work; coarse bands insufficient; adaptive sharding + beds feasible in principle
- [x] Sampled 12 detail pages for empty living-cost examples
- [x] Listed full scrapeable metadata catalogue (search meta, search card, detail `propertyData`, analytics mirror)
- [x] Deep interview (5 rounds) → crystallised spec artefact

## 5. Current Work in Progress

- Nothing in progress. Research session closed.
- **Next session candidate [HIGH]:** Decide product next step (still research vs implement scraper vs licensed data) — not decided.
- **If implementing later [MEDIUM]:** Extend `Listing` / migrations for beds, tenure, lease years, living costs; add Rightmove parse path that emits drafts; keep network out of unit tests via recorded HTML/JSON fixtures.

## 6. Critical Learnings & Gotchas

- ❌ **Don't:** Assume you can paginate all ~61k London results from one `find.html` URL — UI/API only expose ~42 pages (~1008 listings).
- ✅ **Do:** Treat coverage as union of **complete shards** (`resultCount ≤ 1008`), then paginate each; dedupe by listing `id` at band boundaries.
- ❌ **Don't:** Expect `displaySize` / `livingCosts.*` to be populated — often null even for leasehold flats.
- ✅ **Do:** Prefer detail `address.outcode`/`incode` and `sizings[]` over search `displayAddress`/`displaySize` when present.
- 🔍 **Discovery:** Search and detail use **different embed formats** (`__NEXT_DATA__` vs packed `__PAGE_MODEL`).
- 🔍 **Discovery:** Detail `propertyData.termsOfUse` states the embedded API is for Rightmove only; `robots.txt` disallows `/api/*` but not broadly `find.html` / `/properties/{id}` — not a permission grant. User deferred legal for this research.
- ⚠️ **Watch out:** `yearsRemainingOnLease` can be `0` or `null` on leaseholds; freeholds may show `0`. Ground rent was null on all 12 sampled details.
- ⚠️ **Watch out:** Featured/auction/new-home listings skew search pages; sort and filters matter for shard completeness.
- ⚠️ **AskQuestion tool** was unavailable in this agent session; interview used numbered chat options instead.

## 7. Dependencies & Technical Context

- Stack: Python (`uv`) + FastAPI API + Next.js web + SQLite; scraper is a manual CLI tool package.
- No new libraries added this session.
- No DB/schema/API changes.
- Fetch method that worked: `curl` with a normal Chrome User-Agent (Python `urllib` hit SSL cert issues in this environment).
- Example search URL studied:  
  `https://www.rightmove.co.uk/property-for-sale/find.html?locationIdentifier=REGION%5E87490&channel=BUY&transactionType=BUY&...`
- Example detail: `https://www.rightmove.co.uk/properties/88696923`

**Core economics → keys (quick map):**

| Interest                     | Primary keys                                                                                             |
| ---------------------------- | -------------------------------------------------------------------------------------------------------- |
| Price                        | search `price.amount`; detail `prices.primaryPrice`, `displayPriceQualifier`, `mortgageCalculator.price` |
| Beds                         | `bedrooms`                                                                                               |
| Location/postcode            | detail `address.outcode`/`incode`; search `displayAddress` + lat/lng                                     |
| Size                         | detail `sizings[]`; search `displaySize` (sparse); `prices.pricePerSqFt`                                 |
| Tenure/lease                 | detail `tenure.tenureType`, `yearsRemainingOnLease`                                                      |
| Service charge / ground rent | detail `livingCosts.annualServiceCharge`, `annualGroundRent` (+ review fields)                           |

## 8. Open Questions & Blockers

- [HIGH] Should a future build scrape Rightmove despite ToS wording, use licensed data, or stay fixture-only?
- [MEDIUM] Minimum viable schema extension beyond current `Listing` for core economics?
- [MEDIUM] Adaptive shard strategy defaults (price bisect vs borough/outcode vs beds-first)?
- [LOW] Optional completeness spot-check across a larger detail sample (interview left optional).
- No active blockers for further research; implementation blocked only by product/legal choice.

## 9. Reference Materials

- Interview spec: `.cursor/artefacts/interviews/2026-07-22_00-52-54_rightmove-data-interest_interview.md`
- Repo guides: `AGENTS.md`, `docs/STRUCTURE.md`, `tools/scraper/AGENTS.md`
- Rightmove ToS (linked from payload): https://www.rightmove.co.uk/this-site/terms-of-use.html
- robots.txt: https://www.rightmove.co.uk/robots.txt

## 10. Code Snippets for Continuity

**Unpack detail `__PAGE_MODEL` (pattern used in session):**

```python
# window.__PAGE_MODEL = {"data": "<stringified packed array>", "encoding": ...}
# packed[0] is {key: index, ...}; other slots are values or nested index refs
wrapper = json.loads(page_model_object_blob)
packed = json.loads(wrapper["data"])

def unpack(packed):
    root = packed[0]
    memo = {}
    def resolve(idx, stack=None):
        if stack is None:
            stack = set()
        if not isinstance(idx, int):
            return idx
        if idx in memo:
            return memo[idx]
        if idx in stack or idx < 0 or idx >= len(packed):
            return None if idx in stack else idx
        stack.add(idx)
        node = packed[idx]
        if isinstance(node, dict):
            out = {k: resolve(v, stack) for k, v in node.items()}
        elif isinstance(node, list):
            out = [resolve(v, stack) for v in node]
        else:
            out = node
        stack.remove(idx)
        memo[idx] = out
        return out
    return {k: resolve(v) for k, v in root.items()} if isinstance(root, dict) else resolve(0)

model = unpack(packed)
property_data = model["propertyData"]
```

**Search extraction:**

```python
# __NEXT_DATA__ script JSON
properties = data["props"]["pageProps"]["searchResults"]["properties"]
# pagination cap signal:
# searchResults.pagination.total == 42 and max option value == "984"
# fully paginable shard iff int(resultCount.replace(",", "")) <= 1008
```

**Price filter params that work:** `minPrice`, `maxPrice` (GBP integers as query params); optionally `minBedrooms` / `maxBedrooms`.
