# London Home Finder

A local-first tool for collecting and exploring homes for sale in London.
It is designed to run from the same checked-out repository on macOS or Windows.

The repository contains these applications:

- `apps/api` — a FastAPI API backed by SQLite.
- `apps/db` — Alembic migrations for the shared SQLite database.
- `apps/web` — a Next.js App Router frontend.

Listing domain and persistence live in `libs/listings`, shared SQLAlchemy
instrumentation in `libs/db`, the generated TypeScript API client in
`libs/api-client`, and manually invoked data-ingestion commands in
`tools/scraper`.

## Getting started

Install Python 3.13, Node.js 24, uv, and pnpm, then run:

```shell
uv sync --all-packages
pnpm install
uv run just generate-contract
uv run just check
```

Start the applications in separate terminals:

```shell
uv run just dev-api
uv run just dev-web
```

`dev-api` applies the Alembic migrations to `data/london-home-finder.sqlite3`
before starting the local server.

Run `uv run just --list` for all repository commands. See
`docs/STRUCTURE.md` before adding or moving a package.
