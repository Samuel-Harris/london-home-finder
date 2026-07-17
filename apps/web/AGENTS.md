# apps/web — Agent Guide

Purpose: local Next.js App Router frontend for London Home Finder.
Dependencies: may import backend behavior only through `@lhf/api-client`.
Commands: `pnpm --filter @lhf/web lint` · `pnpm --filter @lhf/web typecheck` · `pnpm --filter @lhf/web test`.
Always: keep UI behavior in `src/app` and add user-visible behavior tests in `tests`.
Ask first: add a Next.js route handler, Server Action, or another internal package dependency.
Never: duplicate FastAPI business logic or import `libs/api-client/src` directly.
