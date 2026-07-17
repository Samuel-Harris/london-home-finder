# Changing this repository's structure

The layout and dependency rules are intentional but mutable. Every structural
change ends with `uv run just check` passing and the root `AGENTS.md` updated.

## Current dependency direction

```text
apps/api ───────┐
                ├──> libs/backend
tools/scraper ──┘

apps/web ──────────> libs/api-client ──generated from──> contracts/openapi.json
```

`apps/api` and `tools/scraper` are independent siblings. Python cross-package
dependencies must be both permitted by Import Linter and declared in the
importer's `pyproject.toml`. TypeScript dependencies must be permitted by
dependency-cruiser and declared in the importer's `package.json`.

## Adding a module or package

1. Create the package with a `src/` layout, colocated `tests/`, its own manifest,
   and a short `AGENTS.md`.
2. Add it to the uv or pnpm workspace and register its source with Tach, Import
   Linter, or dependency-cruiser as applicable.
3. Declare only dependencies the package actually imports. Use workspace sources
   or the `workspace:*` protocol for internal dependencies.
4. Add the package to `.github/CODEOWNERS`, the root repository map, and
   `tools/check_structure.py`.
5. Deliberately violate any new boundary once and confirm the boundary command
   reports a legible file-and-line failure. Remove the violation and run
   `uv run just check`.

Use `libs/backend` as the Python sample package: it has a public `api` module,
private implementation modules, pure domain functions, persistence code, tests,
and enforced public-interface boundaries.

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

The API owns the single Alembic history under `apps/api/alembic`. Persistence
models live in `libs/backend`; the API and scraper both use the library's public
interface. Create migrations through the API-owned command and validate them in
the temporary-file SQLite integration tests.

## Keeping instructions current

Every structure change updates affected `AGENTS.md` files in the same change.
`tools/check_structure.py` verifies package instruction files, manifests, and
canonical task names; it also reconciles uv, pnpm, Tach, Import Linter,
dependency-cruiser, and CODEOWNERS registrations with the package tree so
instruction and boundary drift fail in CI.
