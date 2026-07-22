# libs/repository - Agent Guide

Purpose: shared `Repository` protocol for upsert/list persistence surfaces.
Layer: lowest shared library; never import apps, tools, feature libs, or `lhf.db`.
Public modules: `lhf.repository.protocol` — import directly; no barrel `api` module.
Commands: `uv run pytest libs/repository/tests` and `uv run pyright libs/repository`.
Conventions: keep protocols generic over draft and entity types; no SQLAlchemy here.
Never: add feature-specific models or concrete repository implementations.
