# Recon artefact

Write this file to `.cursor/artefacts/scrapes/{source}-recon.md` before any scraper code. `{source}` is a lowercase slug (`rightmove`, `zoopla`).

```markdown
# Recon: {source}

## URLs
- Search:
- Detail:

## Fetch
- Client that returned the embed (curl / Playwright Chrome / Playwright Chromium):
- Status codes:
- Markers present:
- Challenge or interstitial?:

## Embeds
- Search format (e.g. `__NEXT_DATA__` path):
- Detail format (e.g. `window.__PAGE_MODEL`):
- Search and detail differ?:

## Pagination
- Page size:
- Last working index:
- Advertised resultCount:
- Reachable rows:
- Empty-page sentinel:
- In-cap iff:

## Filters that change resultCount
- Params proved:
- Split order if capped:

## Field map
| Interest | Primary key | Fallback | Search or detail | Null policy |
| -------- | ----------- | -------- | ---------------- | ----------- |
|          |             |          |                  |             |

## Sparsity (n ≥ 10 details)
| Field | Non-null count | Notes |
| ----- | -------------- | ----- |

## robots.txt and terms
- robots.txt URL and relevant Disallow:
- HTML search/detail allowed?:
- In-payload termsOfUse (quote, do not interpret as permission):
- Chosen surface (HTML paths only):

## Coverage the user asked for
- Window (location, price, beds, type, tenure, or equivalent):
```

Do not proceed to Phase C if this file is missing, or if Pagination, Field map, or robots.txt rows are empty.
