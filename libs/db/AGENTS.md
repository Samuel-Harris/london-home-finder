# libs/db - Agent Guide

Purpose: shared SQLAlchemy Base, metadata, and SQLite session factory (WAL / FK / busy_timeout).
Layer: lowest Python persistence layer; never import apps, tools, or feature libraries.
Public modules: `lhf.db.base`, `lhf.db.session` — import these directly; no barrel `api` module.
Commands: `uv run pytest libs/db/tests` and `uv run pyright libs/db`.
Conventions: no feature tables here; ORM models live in feature libs and subclass `Base`.
Never: add domain types, repositories, Alembic configuration, or re-export barrels.
