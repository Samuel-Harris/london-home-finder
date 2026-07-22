# Changing this repository's structure

The layout and dependency rules are intentional but mutable. Every structural
change ends with `uv run just check` passing and the root `AGENTS.md` updated.

## Current dependency direction

```text
apps/api ────────────┐
tools/scraper ───────┼──> libs/listings ──> libs/db
apps/db (migrations) ┘         │
                               └──> libs/repository

apps/web ──────────> libs/api-client ──generated from──> contracts/openapi.json
```

`apps/api`, `apps/db`, and `tools/scraper` are independent siblings. Python
cross-package dependencies must be both permitted by Import Linter and declared
in the importer's `pyproject.toml`. TypeScript dependencies must be permitted by
dependency-cruiser and declared in the importer's `package.json`.

Callers import concrete modules that own symbols (for example `lhf.db.session`,
`lhf.listings.listing`). Do not add Python barrel re-export modules. Every Python
workspace package contributes one subpackage under the shared `lhf` namespace
(PEP 420; no `lhf/__init__.py`), for example `libs/db/src/lhf/db`.

## Adding a module or package

1. Create the package with a `src/lhf/<name>/` layout under the shared `lhf`
   namespace (no `lhf/__init__.py`), colocated `tests/`, its own manifest, and a
   short `AGENTS.md`.
2. Add it to the uv or pnpm workspace and register its source with Tach, Import
   Linter, or dependency-cruiser as applicable.
3. Declare only dependencies the package actually imports. Use workspace sources
   or the `workspace:*` protocol for internal dependencies.
4. Add the package to the root repository map and `tools/check_structure.py`.
5. Deliberately violate any new boundary once and confirm the boundary command
   reports a legible file-and-line failure. Remove the violation and run
   `uv run just check`.

Use `libs/listings` as the Python feature-library sample: public modules own
concrete types and behaviour, private `_*.py` modules stay package-local, domain
functions stay pure, and feature-owned ORM models subclass `lhf.db.base.Base`.
Concrete repositories implement `lhf.repository.protocol.Repository` (for example
`ListingRepository`). Use `libs/db` as the shared instrumentation sample (`base`,
`session`) and `libs/repository` for the shared persistence protocol.

## Splitting a module

Introduce the new module beside the old one, move code behind stable interfaces
incrementally, keep boundaries green, and delete the old path only after all
callers have moved. Do not introduce a compatibility wrapper without a verified
consumer and an agreed removal date.

## Changing a contract or dependency direction — ask first

Change the permitted edge first, migrate imports, then remove the old edge.
Regenerate the API contract with `uv run just generate-contract`; generated
files are never edited manually. A temporary exception must name its owner and
removal condition.

## Database changes

`libs/db` owns the shared SQLAlchemy `Base`, `metadata`, and SQLite session
factory (WAL / foreign keys / `busy_timeout`). Feature libraries own their ORM
models and repositories; every model subclasses the one `Base` from `lhf.db.base`
so tables register on the shared `metadata`.

`apps/db` owns the single Alembic history. `lhf.db_app.models` must import each
feature model module (for example `lhf.listings._listing_row`) so shared
`metadata` includes every table; Alembic `env.py` reads metadata from that
module. Adding a future feature library with tables means: define models there,
declare the dependency from `apps/db`, and import the model module in
`lhf.db_app.models`.

Create migrations through the `apps/db`-owned command
(`uv run python -m lhf.db_app.migrations`) and validate them in the temporary-file
SQLite integration tests. `apps/db` is a migration composition root only — not an
HTTP database service.

## Keeping instructions current

Every structure change updates affected `AGENTS.md` files in the same change.
`tools/check_structure.py` verifies package instruction files, manifests, and
canonical task names; it also reconciles uv, pnpm, Tach, Import Linter, and
dependency-cruiser registrations with the package tree so instruction and
boundary drift fail in CI.
