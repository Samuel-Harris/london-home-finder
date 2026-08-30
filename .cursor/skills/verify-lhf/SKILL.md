---
name: verify-lhf
description: Drive London Home Finder the way a user does — isolated Next.js home page plus FastAPI /health and /listings — to prove a change works. Use when verifying UI or API behaviour, capturing screenshots or response bodies, or checking that launch still works after a change.
---

# Verify London Home Finder

Drive the real apps, not unit tests. Launch an isolated pair of processes, exercise one mapped feature the way a user would, capture evidence, then tear down only what this run started.

Primary surface: the Next.js home page. Supporting surface: the FastAPI API. Do not treat `just scrape` as a verification path — it hits live Rightmove.

## Launch

From the repository root:

```bash
uv run python .cursor/skills/verify-lhf/scripts/control_lhf.py launch
```

That command:

1. Refuses if ports `18780` (API) or `18781` (web) are already bound, or if a previous isolated instance is still healthy.
2. Creates a disposable SQLite database under `/tmp/lhf-verify-*` and migrates it with `python -m lhf.db_app.migrations`.
3. Starts `uvicorn lhf.api.app:app` with `LHF_DATABASE_PATH` pointing at that file, host `127.0.0.1`, port `18780`, no reload.
4. Starts `pnpm --filter @lhf/web dev --port 18781 --hostname 127.0.0.1` with `NEXT_PUBLIC_API_URL=http://127.0.0.1:18780`.
5. Waits until `GET /health` returns `{"status":"ok"}` and `GET http://127.0.0.1:18781/` contains the home heading.
6. Writes `.cursor/artefacts/verify-lhf/instance.json` and prints `run_id`, URLs, pids, `database_path`, and `evidence_dir`.

Ready means those two HTTP checks pass. First web compile can take up to 90 seconds.

Never drive `http://localhost:8000` or `http://localhost:3000`. Those are the developer's shared `just dev-api` / `just dev-web` session. Only drive the URLs printed by `launch`.

Only one isolated instance can run: ports are fixed. If launch refuses, run `cleanup` or stop whatever owns 18780/18781. Do not kill processes by name.

## Doctor

```bash
uv run python .cursor/skills/verify-lhf/scripts/control_lhf.py doctor
```

Require exit code 0 and `ok: true` before driving. Doctor checks:

- `instance.json` exists (otherwise nothing from this run is registered).
- The recorded API and web pids are alive.
- `GET {api_url}/health` is `200` with body `{"status":"ok"}`.
- `GET {web_url}/` is `200`, contains `Find a London home with the evidence in one place.`, and shows the isolated API URL (`http://127.0.0.1:18780`).
- The recorded database file exists and is not `data/london-home-finder.sqlite3`.

If anything looks off, run doctor first. Do not keep driving a failing instance.

## Drive

Read `features/README.md`, then the feature file for the behaviour under test. Every recipe starts from the launched baseline unless it says otherwise.

```bash
uv run python .cursor/skills/verify-lhf/scripts/control_lhf.py http get /health --out "$EVIDENCE/health.json"
uv run python .cursor/skills/verify-lhf/scripts/control_lhf.py http get /listings --out "$EVIDENCE/listings.json"
uv run python .cursor/skills/verify-lhf/scripts/control_lhf.py seed-listing
uv run python .cursor/skills/verify-lhf/scripts/control_lhf.py browser snapshot --path "$EVIDENCE/home.aria.txt"
uv run python .cursor/skills/verify-lhf/scripts/control_lhf.py browser screenshot --path "$EVIDENCE/home.png"
```

`$EVIDENCE` is the `evidence_dir` printed by launch (`.cursor/artefacts/verify-lhf/<run_id>/`).

- `http get` talks to the isolated API only.
- `browser snapshot` and `browser screenshot` open Chromium, go to `{web_url}/` (or `--route`), wait for the home heading, then write the artefact.
- `seed-listing` is fixture setup: it replaces all rows in the isolated database with one known listing. It is not a user action and is not proof by itself.

Stable handles:

- Heading: role `heading`, name `Find a London home with the evidence in one place.`
- Eyebrow text: `Local research workspace`
- API URL: a `code` element whose text is `http://127.0.0.1:18780`
- Health body: `{"status":"ok"}`
- Seeded listing: `external_id` `verify-1`, `display_address` `12 Verify Street, Hackney`, `asking_price_gbp` `450000`

## Evidence

Proof artefacts go in `.cursor/artefacts/verify-lhf/<run_id>/` (gitignored). Cleanup must not delete that directory.

Standards:

- Exercise the real user path: open the home page in a browser, or `GET` `/health` and `/listings` as an API client would. Do not call repository methods or TestClient and call that verification.
- Capture the action and the resulting state (ARIA snapshot plus screenshot for UI; status plus body for HTTP). A final screenshot without the request/response is not enough for API features.
- For `list-listings`, prove the JSON body after seed (and the empty array before seed). The home page does not render listings.
- Do not run `just scrape` or any live Rightmove fetch as verification. Seeding through `seed-listing` is the isolated fixture; scrape is an operator ingest against the public web.

## Cleanup

```bash
uv run python .cursor/skills/verify-lhf/scripts/control_lhf.py cleanup
```

Sends SIGTERM (then SIGKILL) to the process groups recorded in `instance.json`, deletes the disposable `/tmp/lhf-verify-*` directory, and removes `instance.json`. It does not delete `evidence_dir`. After cleanup, confirm the screenshot or JSON files are still on disk.

If launch fails part-way, run cleanup anyway so ports are not left bound.

## Helpers

Always invoke the helper through `uv run` from the repository root so workspace packages resolve:

```bash
uv run python .cursor/skills/verify-lhf/scripts/control_lhf.py launch
uv run python .cursor/skills/verify-lhf/scripts/control_lhf.py doctor
uv run python .cursor/skills/verify-lhf/scripts/control_lhf.py http get /health
uv run python .cursor/skills/verify-lhf/scripts/control_lhf.py http get /listings
uv run python .cursor/skills/verify-lhf/scripts/control_lhf.py seed-listing
uv run python .cursor/skills/verify-lhf/scripts/control_lhf.py browser snapshot --path .cursor/artefacts/verify-lhf/probe/home.aria.txt
uv run python .cursor/skills/verify-lhf/scripts/control_lhf.py browser screenshot --path .cursor/artefacts/verify-lhf/probe/home.png
uv run python .cursor/skills/verify-lhf/scripts/control_lhf.py cleanup
```

Playwright Chromium must already be installed (`uv run playwright install chromium` from the README). The helper does not install browsers.
