from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from lhf_api.app import create_app


def render_openapi() -> str:
    return json.dumps(create_app().openapi(), indent=2, sort_keys=True) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate the canonical OpenAPI contract.")
    parser.add_argument("output", type=Path)
    parser.add_argument("--check", action="store_true")
    arguments = parser.parse_args(argv)
    rendered = render_openapi()

    if arguments.check:
        current_contract = (
            arguments.output.read_text(encoding="utf-8") if arguments.output.is_file() else None
        )
        if current_contract != rendered:
            raise SystemExit(f"{arguments.output} is stale; run `uv run just generate-contract`.")
        return 0

    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
