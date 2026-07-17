# libs/api-client — Agent Guide

Purpose: generated TypeScript bindings for the canonical FastAPI OpenAPI contract.
Public interface: consumers import only `@lhf/api-client`; `src/index.ts` owns exports.
Commands: `pnpm --filter @lhf/api-client generate` · `pnpm --filter @lhf/api-client check:generated` · `pnpm --filter @lhf/api-client test`.
Always: regenerate after `contracts/openapi.json` changes and commit the resulting files.
Ask first: change the generator, HTTP client, or package export surface.
Never: hand-edit `src/generated` or import any deployable application.
