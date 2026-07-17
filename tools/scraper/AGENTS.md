# tools/scraper - Agent Guide

Purpose: manually invoked commands that ingest recorded home data.
Layer: tool; may import only the public `lhf_backend.api` surface.
Commands: `uv run pytest tools/scraper/tests` and `uv run pyright tools/scraper`.
Conventions: keep parsing deterministic and network access out of tests.
Never: import the API app or create a background service.
