# libs/listings - Agent Guide

Purpose: listing domain types, SQLite ORM models, and repository.
Layer: feature library above `libs/db` and `libs/repository`; never import apps or tools.
Public modules: `lhf.listings.listing`, `lhf.listings.listing_repository` — import these
directly; no barrel `api` module. `_listing_row` stays package-private (plus `lhf.db_app`).
Commands: `uv run pytest libs/listings/tests` and `uv run pyright libs/listings`.
Conventions: ORM models subclass `Base` from `lhf.db.base`; `ListingRepository`
implements `Repository` from `lhf.repository.protocol`; keep domain calculations pure.
Never: own Alembic history, shared session-factory implementation, or re-export barrels.
