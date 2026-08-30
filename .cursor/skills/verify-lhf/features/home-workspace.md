# Home workspace

The home page is the only browser surface. It introduces the local research workspace, states the product purpose, and shows which API URL the frontend is configured to use.

## Sub-features

- `home-open` loads `/` and shows the product heading.
- `home-identity` shows the eyebrow `Local research workspace` and the supporting lede.
- `home-api-url` shows `API connection:` followed by the isolated API origin in a `code` element.

## How to get to it (user POV)

- Open `http://127.0.0.1:18781/` in a browser after launch.

## Driving it with control_lhf

Preconditions:

- London Home Finder is healthy at `http://127.0.0.1:18781`.
- `control_lhf.py doctor` reports `ok: true` and `web_url: http://127.0.0.1:18781`.
- Evidence will be written under the `evidence_dir` from launch.

- **Open home.** Load `/`. Run `uv run python .cursor/skills/verify-lhf/scripts/control_lhf.py browser snapshot --path "$EVIDENCE/home.aria.txt"`. The snapshot includes a heading named `Find a London home with the evidence in one place.`
- **Confirm identity.** The same snapshot includes the text `Local research workspace` and the lede that begins `Compare collected listings`.
- **Confirm API connection.** The snapshot includes `API connection:` and `http://127.0.0.1:18781` must not appear as the API origin; the `code` value is `http://127.0.0.1:18780`.
- **Proof.** Capture the rendered page. Run `uv run python .cursor/skills/verify-lhf/scripts/control_lhf.py browser screenshot --path "$EVIDENCE/home.png"`. The screenshot shows the heading, the eyebrow, and `API connection: http://127.0.0.1:18780`.

## Gotchas

- A 200 from the Next.js process is not proof if the heading is missing; doctor already requires the heading, but a mid-compile HTML shell can still be empty if you skip doctor.
- The shared `just dev-web` instance on port 3000 shows `http://localhost:8000` by default. That is a different instance. Do not treat it as this feature.
- The home page does not list properties. Do not fail this feature because `/listings` is empty.
