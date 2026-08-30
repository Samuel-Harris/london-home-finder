---
name: html-source-scrape
description: >-
  Investigate a public HTML listing or marketplace site, then build a
  fail-closed scraper. Forces recon (raw HTML, embeds, pagination caps,
  field map, robots/ToS) before fetch/parse/map/persist, then a live scrape
  with default filters. Use when the user names a site such as Rightmove
  or Zoopla, asks to scrape or ingest a data source, or wants to
  reverse-engineer a listing page that is not a documented API.
---

# HTML source scrape

Investigate first. Build second. Prove with a live scrape. Skipping recon is a failure.

Copy this checklist and keep it in the conversation:

```text
- [ ] Phase A recon artefact written
- [ ] Product decisions known (or /deep-interview done)
- [ ] Fetch, parse, map, persist split
- [ ] Recorded-HTML tests, no network, no browser
- [ ] Live scrape with default filters
- [ ] /thermos on the branch diff, justified findings applied
```

## Hard rules

- Save **raw HTML**. Accessibility snapshots and markdown captures strip `__NEXT_DATA__` and `window.__*` payloads.
- Look for JSON in `<script>` tags and `window.*` assignments before CSS or XPath card parsers.
- Record robots.txt and in-payload terms of use in the recon artefact. Then fetch HTML listing pages unless robots forbids those URLs. Never call vendor `/api/*`. That observation is not a licence.
- Persist isolation is per source. `replace_source` must not delete another source's rows. If a run is wrong, scrape again.
- Identity (`source`, `external_id`, `url`) required. Economics nullable. Keep sparse rows.
- Tests never use the network and never launch Chromium.
- One user entrypoint. No second ingest contract.

In this repository, `tools/scraper/AGENTS.md` owns `just scrape`, the default window, Playwright, shards, and `--resume`. Do not copy that contract here. Follow it when the build is in this repo. `listings` is the shared snapshot with unique `(source, external_id)`. Isolate with `replace_source`. Do not add a second isomorphic listings table.

## Phase A. Recon

No schema. No persist. No scraper package until the artefact exists.

1. Fetch one search page and one detail page as raw HTML. Start with curl and a normal browser User-Agent. If the embed is missing or the response is 403, escalate to Playwright with system Chrome then bundled Chromium. Stop and report if the HTML still lacks the markers or is a challenge page.
2. Search the HTML for `__NEXT_DATA__`, `application/ld+json`, `application/json` script tags, and `window.__` assignments. Search and detail often use different embeds.
3. Inventory keys. Sample at least 10 detail pages for null rates on fields the user cares about. Do not design required columns from one happy-path page.
4. Walk pagination until it dies. Record page size, last working index, advertised `resultCount` vs rows actually returned, and the empty-page sentinel. Do not trust `resultCount` as reachable rows.
5. Probe filter query params until a shard's `resultCount` fits under the cap, or prove it never will without splitting.
6. Write the field map (user interest → primary key → fallback → null policy, search vs detail).
7. Write the recon artefact from [references/recon-artefact.md](references/recon-artefact.md) to `.cursor/artefacts/scrapes/{source}-recon.md`.

**Stop.** Do not write fetch, parse, map, or persist modules until that file exists.

Rightmove-shaped sites: read [references/worked-example-rightmove.md](references/worked-example-rightmove.md) after the HTML is saved. Do not start from those keys.

## Phase B. Interview if product is vague

If coverage, search vs detail, named columns vs blob, skip vs null incomplete rows, or replace vs upsert are unstated, stop and follow `.cursor/skills/deep-interview/SKILL.md`.

Do not interview a measured page cap. If `resultCount` exceeds the reachable page limit, shard the user's filter until each shard is in-cap. That is engineering. Fail closed if a shard cannot be split further.

## Phase C. Build

1. Pure parse modules. Input is `html: str`. Output is a frozen dataclass (search card, detail record). No vendor dicts past this boundary. Defensive JSON coercion lives in one helper module.
2. Map owns policy (prefer detail, sentinel zeros → null, unit conversion, invalid postcode → null).
3. Fetcher isolated. Tests fake `get`. Lazy-start the browser on first real request. Escalate to Playwright only if recon proved it necessary. Retry timeouts and 5xx. Fail immediately on 4xx. After a poisoned navigation (`chrome-error://`), close the tab and open a new one. Check HTTP status; `page.goto` does not throw on 403. Distinguish blocked HTML (zero cards, no embed) from a real empty result set.
4. Persist once, atomically, with `replace_source`. Fail closed. A failed or empty crawl must not wipe the previous snapshot. Checkpoint job progress in a sidecar JSON beside the DB (`*.tmp` then `os.replace`), not in the listings schema. Dedupe by vendor id. Drop featured leakage whose known price is outside the **window**. Keep POA.
5. If the cap is real, adaptive-split the user's filter (price first, then the next discrete filter) until each shard is complete. Union unique ids. Fail if unsplittable.
6. Wire one user command. Move domain, API, and migrations in the same change when columns change.
7. Record fixtures from live HTML (script payload only if the page is huge). When a live run shows 0% on a field that recon sampled as present, re-fetch one live page and diff keys against the fixture.

## Phase D. Prove

Run the scraper with the product's default filters against the working database. Query that source's rows.

Query the snapshot: unique vendor ids, URL matches id, identity complete, price bounds, coverage vs recon sample. 0% on a field that recon saw is a parser bug. Sparse-but-nonzero is usually the vendor.

`verify-lhf` must not run this scrape. That skill seeds an isolated DB. This skill is operator ingest.

## Review

After the build, follow `.cursor/skills/thermos/SKILL.md` on the branch diff. Apply justified findings. A pre-written "keep files small" bullet list is not that review.

## Additional resources

- Recon template: [references/recon-artefact.md](references/recon-artefact.md)
- Rightmove worked example: [references/worked-example-rightmove.md](references/worked-example-rightmove.md)
- This repo's ingest contract: `tools/scraper/AGENTS.md`
- Interview: `.cursor/skills/deep-interview/SKILL.md`
- Diff review: `.cursor/skills/thermos/SKILL.md`
