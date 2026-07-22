default: check

install:
    uv sync --all-packages
    pnpm install

fmt:
    uv run ruff format .
    uv run ruff check --fix .
    pnpm format

lint:
    uv run ruff check .
    uv run ruff format --check .
    uv run python tools/check_structure.py
    pnpm lint
    pnpm format:check

typecheck:
    uv run pyright
    pnpm typecheck

test:
    uv run pytest
    pnpm test

boundaries:
    uv run tach check-external
    uv run lint-imports
    pnpm boundaries

contract:
    uv run python -m lhf.api.openapi --check contracts/openapi.json
    pnpm --filter @lhf/api-client check:generated

check: lint typecheck boundaries test contract

build:
    pnpm build

generate-contract:
    uv run python -m lhf.api.openapi contracts/openapi.json
    pnpm --filter @lhf/api-client generate

migrate database_path="data/london-home-finder.sqlite3":
    uv run python -m lhf.db_app.migrations "{{database_path}}"

import-fixture fixture database_path="data/london-home-finder.sqlite3":
    uv run python -m lhf.db_app.migrations "{{database_path}}"
    uv run lhf-scrape import-fixture "{{fixture}}" --database "{{database_path}}"

dev-api: migrate
    uv run uvicorn lhf.api.app:app --reload

dev-web:
    pnpm --filter @lhf/web dev

precommit:
    uv run pre-commit run --all-files
