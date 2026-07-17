# libs/backend - Agent Guide

Purpose: shared listing domain and SQLite persistence code.
Layer: lowest Python layer; never import apps or tools.
Public interface: other packages import only `lhf_backend.api`.
Commands: `uv run pytest libs/backend/tests` and `uv run pyright libs/backend`.
Conventions: keep transactions short and domain calculations pure.
Never: add API, CLI, or framework-specific behavior here.
