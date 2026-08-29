default: check

install:
    uv sync --all-packages
    pnpm install
    uv run playwright install chromium

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

[arg("min_price", long="min-price")]
[arg("max_price", long="max-price")]
[arg("min_bedrooms", long="min-bedrooms")]
[arg("property_types", long="property-types")]
[arg("tenure", long="tenure")]
[arg("max_pages", long="max-pages")]
[arg("resume", long="resume", value="true")]
scrape database_path="data/london-home-finder.sqlite3" min_price="350000" max_price="800000" min_bedrooms="2" property_types="detached,semi-detached,terraced,bungalow" tenure="FREEHOLD" max_pages="" resume="":
    uv run python -m lhf.db_app.migrations "{{database_path}}"
    uv run lhf-scrape --database "{{database_path}}" --min-price "{{min_price}}" --max-price "{{max_price}}" --min-bedrooms "{{min_bedrooms}}" --property-types "{{property_types}}" --tenure "{{tenure}}" {{ if max_pages != "" { "--max-pages " + max_pages } else { "" } }} {{ if resume != "" { "--resume" } else { "" } }}

dev-api: migrate
    uv run uvicorn lhf.api.app:app --reload

dev-web:
    pnpm --filter @lhf/web dev

precommit:
    uv run pre-commit run --all-files
