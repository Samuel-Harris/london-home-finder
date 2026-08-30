# List listings

List listings returns every stored home as JSON. An empty isolated database yields an empty array; after the verify fixture is seeded, the same request returns that one listing.

## Sub-features

- `listings-empty` returns `[]` when no listings have been stored.
- `listings-seeded` returns the fixture listing after `seed-listing`.
- `listings-fields` includes `external_id`, `display_address`, and `asking_price_gbp` for the seeded row.

## How to get to it (user POV)

- Request `GET http://127.0.0.1:18780/listings`.

## Driving it with control_lhf

Preconditions:

- London Home Finder API is healthy at `http://127.0.0.1:18780`.
- `control_lhf.py doctor` reports `ok: true`.
- Launch has not seeded listings yet, or you have just launched a fresh instance.

- **Empty list.** Run `uv run python .cursor/skills/verify-lhf/scripts/control_lhf.py http get /listings --out "$EVIDENCE/listings-empty.json"`. Exit code is `0`, `status: 200`, and the body is `[]`.
- **Seed fixture.** Run `uv run python .cursor/skills/verify-lhf/scripts/control_lhf.py seed-listing`. Stdout includes `external_id: verify-1` and `display_address: 12 Verify Street, Hackney`. This is setup, not proof.
- **Seeded list.** Run `uv run python .cursor/skills/verify-lhf/scripts/control_lhf.py http get /listings --out "$EVIDENCE/listings-seeded.json"`. Exit code is `0`, `status: 200`, the JSON array has length 1, `external_id` is `verify-1`, `display_address` is `12 Verify Street, Hackney`, and `asking_price_gbp` is `450000`.
- **Proof.** Keep both JSON files. Empty and seeded responses are required; a seeded body alone does not prove the empty path.

## Gotchas

- `seed-listing` uses `replace_source` and replaces every `verify` row in the isolated database. Do not seed if you still need the empty-list artefact.
- The running API reads SQLite per request. You do not restart after seed.
- The home page does not render this payload. Browser screenshots cannot prove this feature.
- Do not scrape Rightmove to populate listings for verification.
- Do not read `data/london-home-finder.sqlite3`. Doctor must already have refused that path.
