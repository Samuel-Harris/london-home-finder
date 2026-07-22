# London Home Finder - Agent Guide

## Repository map

- `apps/api` — deployable FastAPI composition root.
- `apps/db` — sole Alembic history and migrate CLI composition root.
- `apps/web` — deployable Next.js frontend; may import `libs/api-client` only.
- `libs/db` — shared SQLAlchemy Base, metadata, and SQLite session factory.
- `libs/repository` — shared `Repository` protocol for upsert/list persistence.
- `libs/listings` — listing domain, ORM models, and repository; imports `libs/db`
  and `libs/repository`.
- `libs/api-client` — generated OpenAPI client plus its small handwritten wrapper.
- `tools/scraper` — manually invoked ingestion CLI; may import `libs/listings` and `libs/db`.
- `contracts` — generated OpenAPI contract. Do not edit it by hand.

## Commands

- Install: `uv sync --all-packages` then `pnpm install`
- Format: `uv run just fmt`
- Test: `uv run just test`
- Lint: `uv run just lint`
- Types: `uv run just typecheck`
- Boundaries: `uv run just boundaries`
- All checks: `uv run just check`

## Structural boundaries

- Always declare inter-package dependencies in the importing package manifest.
- Never use Python barrel modules (re-export-only files such as `api.py`). Import the
  concrete module that owns the symbol (for example `lhf.db.base`, `lhf.db.session`,
  `lhf.listings.listing`). Leading-underscore modules stay package-private.
- Python packages share the `lhf` namespace (`lhf.db`, `lhf.listings`, `lhf.api`, …).
- Always import frontend API code through `@lhf/api-client`.
- Ask first before changing dependency direction, adding a top-level directory, or introducing a deployable.
- Never import one app from another, import generated-client internals directly, or edit generated files.
- Follow `docs/STRUCTURE.md` for every package, module, or contract change.

## Working method

- Read every file you will modify and inspect nearby implementations and tests before writing.
- Reuse existing project patterns, libraries, naming, and style. If no relevant pattern exists and the choice is material, explain the options and ask before committing to one.
- State assumptions and success criteria before multi-step work. Surface material tradeoffs and architectural decisions.
- Implement the smallest complete solution. Avoid speculative abstractions, configuration, error handling, compatibility layers, dependencies, and unrelated cleanup.
- Keep diffs surgical. Do not reformat or rename unrelated code. Remove only dead code or imports made obsolete by your change.
- Diagnose from concrete evidence. Reproduce bugs before fixing them, change one causal factor at a time, and address root causes rather than masking symptoms.
- Verify behavior, not implementation details. For bug fixes, add a failing regression test first when practical. Run relevant checks before and after changes and report any pre-existing failures.
- Before adding a dependency, confirm the repository and standard library do not already provide the needed capability. Explain why each new dependency is necessary.
- Report what changed, why, verification evidence, and any precise remaining uncertainty. Do not claim success beyond the checks actually run.

## Compatibility gate

Apply this gate before adding a second public entry point, legacy mode, compatibility parameter, parallel schema, serialization alias, adapter, or wrapper whose purpose is to preserve an old contract.

- Prefer one canonical implementation and contract.
- Add compatibility only for a verified obligation such as a published API, external consumer, or user-approved phased migration.
- If necessity is uncertain, ask which contract must remain supported, for whom, and for how long before implementing it.
- Prefer updating callers, documentation, and persisted contracts in the same change when they are in scope.
- Test-only fixtures and narrow test shims are not compatibility surfaces.

## Plan handoff standard

When creating or refining an implementation plan, make it executable by another agent without product or architectural guesswork.

- Resolve intended behavior, edge cases, failure handling, constraints, non-goals, compatibility, migration, rollout, and success criteria. Ask the user about any unresolved material decision.
- Describe the chosen design, important data flows and invariants, affected callers and artifacts, concrete execution order, and exact verification evidence.
- Name important files, fields, routes, schemas, commands, and tests. Use snippets or diagrams only where they materially remove ambiguity.
- Record rejected alternatives briefly when the choice affects behavior, safety, compatibility, performance, rollout, or maintainability.
- Do not defer decisions with phrases such as "as appropriate", "if needed", or "the implementer can choose".
- End substantial implementation plans with a strict maintainability review and a step to apply justified findings.

## Python guidance

When modifying Python, follow the Zen of Python in practical terms: prefer explicit, simple, flat, readable code; do not silently swallow errors; and do not guess through ambiguity. Practicality beats purity.
