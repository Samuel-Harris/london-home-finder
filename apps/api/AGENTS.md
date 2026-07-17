# apps/api - Agent Guide

Purpose: FastAPI composition root, OpenAPI generation, and Alembic ownership.
Layer: app; may import only the public `lhf_backend.api` surface.
Commands: `uv run pytest apps/api/tests` and `uv run pyright apps/api`.
Conventions: keep routes thin and migrations aligned with backend metadata.
Ask first: change a route contract or migration history.
Never: place domain logic here or import the scraper or web app.
