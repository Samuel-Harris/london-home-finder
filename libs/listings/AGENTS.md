# libs/listings - Agent Guide

Purpose: listing domain types, SQLite ORM models, and repository.
Layer: feature library above `libs/db`; never import apps or tools.
Public modules: `lhf.listings.listing`, `lhf.listings.listing_repository` — import these
directly; no barrel `api` module. `_listing_row` and `_zoopla_listing_row` stay
package-private (plus `lhf.db_app`). Shared column definitions live in
`_listing_columns`.
Commands: `uv run pytest libs/listings/tests` and `uv run pyright libs/listings`.
Conventions: ORM models subclass `Base` from `lhf.db.base`; `ListingRepository` is
the concrete persistence class; keep domain calculations pure. `listings` is
Rightmove; `listings_zoopla` is Zoopla. `replace_all` wipes only `listings`;
`replace_zoopla` wipes only `listings_zoopla`. `list_all` unions both tables
ordered by `(source, external_id)`. `id` is the per-table primary key and can
repeat across sources; listing identity is `(source, external_id)`.
Never: own Alembic history, shared session-factory implementation, or re-export barrels.
