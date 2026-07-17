# London Home Finder

A local-first tool for collecting and exploring homes for sale in London.
It is designed to run from the same checked-out repository on macOS or Windows.

The repository contains two applications:

- `apps/api` — a FastAPI API backed by SQLite.
- `apps/web` — a Next.js App Router frontend.

Reusable backend logic lives in `libs/backend`, the generated TypeScript API
client lives in `libs/api-client`, and manually invoked data-ingestion commands
live in `tools/scraper`.

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
