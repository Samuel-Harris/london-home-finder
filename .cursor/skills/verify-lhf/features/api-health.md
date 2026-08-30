# API health

Health tells a user of the API that the process is up without needing a database file to exist.

## Sub-features

- `health-ok` returns HTTP 200 and `{"status":"ok"}` for `GET /health`.

## How to get to it (user POV)

- Request `GET http://127.0.0.1:18780/health`.

## Driving it with control_lhf

Preconditions:

- London Home Finder API is healthy at `http://127.0.0.1:18780`.
- `control_lhf.py doctor` reports `ok: true` and `api_url: http://127.0.0.1:18780`.

- **Request health.** Run `uv run python .cursor/skills/verify-lhf/scripts/control_lhf.py http get /health --out "$EVIDENCE/health.json"`. Exit code is `0`, stdout includes `status: 200`, and the body is exactly `{"status":"ok"}`.
- **Proof.** The file `$EVIDENCE/health.json` contains `{"status":"ok"}`. Re-read that file after the request; do not trust the process exit code alone.

## Gotchas

- Doctor already called `/health`. That check is a pre-flight, not the feature proof. Capture a dedicated response body in `evidence_dir`.
- `/health` succeeding does not prove listings are readable. Use [List listings](./list-listings.md) for that.
- Do not call the developer's server on port 8000.
