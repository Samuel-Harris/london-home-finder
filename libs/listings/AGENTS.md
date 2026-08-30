# libs/listings - Agent Guide

Purpose: listing domain types, SQLite ORM models, and repository.
Layer: feature library above `libs/db`; never import apps or tools.
Public modules: `lhf.listings.listing`, `lhf.listings.listing_repository` — import these
directly; no barrel `api` module. `_listing_row` stays package-private (plus `lhf.db_app`).
Commands: `uv run pytest libs/listings/tests` and `uv run pyright libs/listings`.
Conventions: ORM models subclass `Base` from `lhf.db.base`; `ListingRepository` is
the concrete persistence class; `replace_source(source, drafts)` deletes only
rows for that `source` then inserts; `list_all` stays unfiltered; keep domain
calculations pure.
Never: own Alembic history, shared session-factory implementation, or re-export barrels.
