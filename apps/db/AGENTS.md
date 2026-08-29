# apps/db - Agent Guide

Purpose: sole Alembic history and migrate CLI for the shared SQLite database.
Layer: app; may import concrete `lhf.db` modules and feature libraries that define tables.
Commands: `uv run pytest apps/db/tests`, `uv run pyright apps/db`, and
`uv run python -m lhf.db_app.migrations <database-path>`.
Conventions: `lhf.db_app.models` must import every feature ORM module so shared
`metadata` includes all tables; Alembic `env.py` imports that module. Adding a
feature lib with tables means declaring the dependency here and importing its ORM
module in `lhf.db_app.models`.
Ask first: change migration history or move Alembic ownership.
Never: expose an HTTP database service or place domain logic here.
