# apps/api - Agent Guide

Purpose: FastAPI composition root and OpenAPI generation.
Layer: app; may import concrete modules from `lhf.listings` and `lhf.db` (not barrels).
Commands: `uv run pytest apps/api/tests` and `uv run pyright apps/api`.
Conventions: keep routes thin; schema changes go through `apps/db` migrations.
Ask first: change a route contract.
Never: own Alembic history, place domain logic here, or import the scraper or web app.
