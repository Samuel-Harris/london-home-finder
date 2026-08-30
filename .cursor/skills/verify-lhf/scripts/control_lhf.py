#!/usr/bin/env python3
"""Launch, inspect, drive, and tear down an isolated London Home Finder instance."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import TypedDict

from lhf.db.session import create_session_factory
from lhf.listings.listing import ListingDraft
from lhf.listings.listing_repository import ListingRepository
from playwright.sync_api import sync_playwright

REPO_ROOT = Path(__file__).resolve().parents[4]
ARTEFACTS_ROOT = REPO_ROOT / ".cursor" / "artefacts" / "verify-lhf"
INSTANCE_PATH = ARTEFACTS_ROOT / "instance.json"
API_PORT = 18780
WEB_PORT = 18781
API_HOST = "127.0.0.1"
WEB_HOST = "127.0.0.1"
HEADING = "Find a London home with the evidence in one place."
SEEDED_EXTERNAL_ID = "verify-1"
SEEDED_ADDRESS = "12 Verify Street, Hackney"
SEEDED_PRICE_GBP = 450000
READY_TIMEOUT_SECONDS = 90.0
STOP_TIMEOUT_SECONDS = 10.0


class InstanceState(TypedDict):
    run_id: str
    api_pid: int
    web_pid: int
    api_url: str
    web_url: str
    database_path: str
    instance_dir: str
    evidence_dir: str


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Drive an isolated London Home Finder instance for verification."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("launch", help="Start API and web on isolated ports.")
    subparsers.add_parser("doctor", help="Check that this run's instance is healthy.")
    http_parser = subparsers.add_parser("http", help="GET a path on the isolated API.")
    http_parser.add_argument("method", choices=["get"])
    http_parser.add_argument("path")
    http_parser.add_argument("--out", type=Path)
    browser_parser = subparsers.add_parser("browser", help="Drive the isolated web UI.")
    browser_parser.add_argument("action", choices=["snapshot", "screenshot"])
    browser_parser.add_argument("--path", type=Path, required=True)
    browser_parser.add_argument("--route", default="/")
    subparsers.add_parser("seed-listing", help="Replace listings with the verify fixture.")
    subparsers.add_parser("cleanup", help="Stop this run's processes and delete instance data.")

    arguments = parser.parse_args(argv)
    commands = {
        "launch": cmd_launch,
        "doctor": cmd_doctor,
        "http": cmd_http,
        "browser": cmd_browser,
        "seed-listing": cmd_seed_listing,
        "cleanup": cmd_cleanup,
    }
    return commands[arguments.command](arguments)


def cmd_launch(_arguments: argparse.Namespace) -> int:
    if INSTANCE_PATH.exists():
        existing = _read_instance()
        if _pids_alive(existing) and _endpoints_ready(existing):
            print(
                "Refusing to launch: an isolated instance is already healthy. "
                "Run cleanup first, or drive the existing instance.",
                file=sys.stderr,
            )
            print(f"api_url: {existing['api_url']}", file=sys.stderr)
            print(f"web_url: {existing['web_url']}", file=sys.stderr)
            return 2
        _stop_instance(existing)

    for port, label in ((API_PORT, "API"), (WEB_PORT, "web")):
        if not _port_free(port):
            print(
                f"Refusing to launch: {label} port {port} is already in use. "
                "Do not drive a shared instance.",
                file=sys.stderr,
            )
            return 2

    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    instance_dir = Path(tempfile.mkdtemp(prefix=f"lhf-verify-{run_id}-"))
    database_path = instance_dir / "lhf.sqlite3"
    evidence_dir = ARTEFACTS_ROOT / run_id
    evidence_dir.mkdir(parents=True, exist_ok=True)
    api_log = instance_dir / "api.log"
    web_log = instance_dir / "web.log"

    try:
        _migrate(database_path)
        api_pid = _start_api(database_path, api_log)
        web_pid = _start_web(web_log)
        state: InstanceState = {
            "run_id": run_id,
            "api_pid": api_pid,
            "web_pid": web_pid,
            "api_url": f"http://{API_HOST}:{API_PORT}",
            "web_url": f"http://{WEB_HOST}:{WEB_PORT}",
            "database_path": str(database_path),
            "instance_dir": str(instance_dir),
            "evidence_dir": str(evidence_dir),
        }
        ARTEFACTS_ROOT.mkdir(parents=True, exist_ok=True)
        _write_instance(state)
        _wait_until_ready(state)
    except Exception:
        if INSTANCE_PATH.exists():
            _stop_instance(_read_instance())
        else:
            _rmtree(instance_dir)
        raise

    _print_state(state)
    return 0


def cmd_doctor(_arguments: argparse.Namespace) -> int:
    state = _require_instance()
    errors: list[str] = []
    if not _pid_alive(state["api_pid"]):
        errors.append(f"api pid {state['api_pid']} is not running")
    if not _pid_alive(state["web_pid"]):
        errors.append(f"web pid {state['web_pid']} is not running")
    health_status, health_body = _http_get(f"{state['api_url']}/health")
    if health_status != 200 or health_body.strip() != '{"status":"ok"}':
        errors.append(f"health unexpected: status={health_status} body={health_body!r}")
    web_status, web_body = _http_get(state["web_url"] + "/")
    if web_status != 200:
        errors.append(f"web unexpected status: {web_status}")
    if HEADING not in web_body:
        errors.append("web is missing the home heading")
    expected_api = state["api_url"]
    if expected_api not in web_body:
        errors.append(f"web is not showing API connection {expected_api}")
    database_path = Path(state["database_path"])
    if not database_path.is_file():
        errors.append(f"database missing: {database_path}")
    if "london-home-finder.sqlite3" in str(database_path):
        errors.append("database path looks like the shared local file; refuse to drive it")
    _print_state(state)
    print(f"health: {health_body.strip()}")
    print(f"web_status: {web_status}")
    if errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        print("ok: false")
        return 1
    print("ok: true")
    return 0


def cmd_http(arguments: argparse.Namespace) -> int:
    state = _require_instance()
    path = arguments.path if arguments.path.startswith("/") else f"/{arguments.path}"
    status, body = _http_get(state["api_url"] + path)
    print(f"status: {status}")
    print(body, end="" if body.endswith("\n") else "\n")
    if arguments.out is not None:
        _write_text(arguments.out, body)
        print(f"wrote: {arguments.out}")
    return 0 if status == 200 else 1


def cmd_browser(arguments: argparse.Namespace) -> int:
    state = _require_instance()
    destination = state["web_url"] + (
        arguments.route if arguments.route.startswith("/") else f"/{arguments.route}"
    )
    output_path = arguments.path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        page.goto(destination, wait_until="networkidle")
        page.get_by_role("heading", name=HEADING).wait_for()
        if arguments.action == "screenshot":
            page.screenshot(path=str(output_path), full_page=True)
        else:
            snapshot = page.locator("main").aria_snapshot()
            _write_text(output_path, snapshot + "\n")
        browser.close()
    print(f"wrote: {output_path}")
    return 0


def cmd_seed_listing(_arguments: argparse.Namespace) -> int:
    state = _require_instance()
    repository = ListingRepository(create_session_factory(state["database_path"]))
    count = repository.replace_source(
        "verify",
        [
            ListingDraft(
                source="verify",
                external_id=SEEDED_EXTERNAL_ID,
                url="https://example.invalid/properties/verify-1",
                display_address=SEEDED_ADDRESS,
                asking_price_gbp=SEEDED_PRICE_GBP,
                bedrooms=2,
                property_type="house",
                postcode="E8 1AB",
                tenure_type="FREEHOLD",
            )
        ],
    )
    print(f"seeded: {count}")
    print(f"external_id: {SEEDED_EXTERNAL_ID}")
    print(f"display_address: {SEEDED_ADDRESS}")
    print(f"asking_price_gbp: {SEEDED_PRICE_GBP}")
    return 0


def cmd_cleanup(_arguments: argparse.Namespace) -> int:
    if not INSTANCE_PATH.exists():
        print("no instance to clean up")
        return 0
    state = _read_instance()
    _stop_instance(state)
    print(f"stopped api_pid={state['api_pid']} web_pid={state['web_pid']}")
    print(f"removed instance_dir: {state['instance_dir']}")
    print(f"kept evidence_dir: {state['evidence_dir']}")
    return 0


def _require_instance() -> InstanceState:
    if not INSTANCE_PATH.exists():
        raise SystemExit(
            "No isolated instance is registered. Run launch first. "
            "Do not drive a server on ports 8000 or 3000."
        )
    return _read_instance()


def _read_instance() -> InstanceState:
    return json.loads(INSTANCE_PATH.read_text(encoding="utf-8"))


def _write_instance(state: InstanceState) -> None:
    INSTANCE_PATH.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def _print_state(state: InstanceState) -> None:
    for key in (
        "run_id",
        "api_url",
        "web_url",
        "database_path",
        "instance_dir",
        "evidence_dir",
        "api_pid",
        "web_pid",
    ):
        print(f"{key}: {state[key]}")


def _migrate(database_path: Path) -> None:
    subprocess.run(
        ["uv", "run", "python", "-m", "lhf.db_app.migrations", str(database_path)],
        cwd=REPO_ROOT,
        check=True,
    )


def _start_api(database_path: Path, log_path: Path) -> int:
    environment = os.environ.copy()
    environment["LHF_DATABASE_PATH"] = str(database_path)
    with log_path.open("w", encoding="utf-8") as log_file:
        process = subprocess.Popen(
            [
                "uv",
                "run",
                "uvicorn",
                "lhf.api.app:app",
                "--host",
                API_HOST,
                "--port",
                str(API_PORT),
            ],
            cwd=REPO_ROOT,
            env=environment,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    return process.pid


def _start_web(log_path: Path) -> int:
    environment = os.environ.copy()
    environment["NEXT_PUBLIC_API_URL"] = f"http://{API_HOST}:{API_PORT}"
    with log_path.open("w", encoding="utf-8") as log_file:
        process = subprocess.Popen(
            [
                "pnpm",
                "--filter",
                "@lhf/web",
                "dev",
                "--port",
                str(WEB_PORT),
                "--hostname",
                WEB_HOST,
            ],
            cwd=REPO_ROOT,
            env=environment,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    return process.pid


def _wait_until_ready(state: InstanceState) -> None:
    deadline = time.monotonic() + READY_TIMEOUT_SECONDS
    last_error = "timed out waiting for API and web"
    while time.monotonic() < deadline:
        if not _pids_alive(state):
            raise RuntimeError(_startup_failure(state, "a launched process exited"))
        web_log = Path(state["instance_dir"]) / "web.log"
        log_text = ""
        if web_log.is_file():
            log_text = web_log.read_text(encoding="utf-8", errors="replace")
        if "Invalid project directory" in log_text or "ERR_PNPM" in log_text:
            raise RuntimeError(_startup_failure(state, "web process failed to start"))
        if _endpoints_ready(state):
            return
        last_error = "endpoints not ready yet"
        time.sleep(0.4)
    raise RuntimeError(_startup_failure(state, last_error))


def _endpoints_ready(state: InstanceState) -> bool:
    health_status, health_body = _http_get(f"{state['api_url']}/health")
    if health_status != 200 or health_body.strip() != '{"status":"ok"}':
        return False
    web_status, web_body = _http_get(state["web_url"] + "/")
    return web_status == 200 and HEADING in web_body


def _startup_failure(state: InstanceState, reason: str) -> str:
    api_log = Path(state["instance_dir"]) / "api.log"
    web_log = Path(state["instance_dir"]) / "web.log"
    return (
        f"launch failed: {reason}\n"
        f"api log ({api_log}):\n{_tail(api_log)}\n"
        f"web log ({web_log}):\n{_tail(web_log)}"
    )


def _tail(path: Path, lines: int = 40) -> str:
    if not path.is_file():
        return "(missing)"
    content = path.read_text(encoding="utf-8", errors="replace").splitlines()
    return "\n".join(content[-lines:]) or "(empty)"


def _http_get(url: str) -> tuple[int, str]:
    request = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status, response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        return error.code, error.read().decode("utf-8", errors="replace")
    except (TimeoutError, urllib.error.URLError, OSError):
        return 0, ""


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _port_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((API_HOST, port))
        except OSError:
            return False
    return True


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _pids_alive(state: InstanceState) -> bool:
    return _pid_alive(state["api_pid"]) and _pid_alive(state["web_pid"])


def _stop_instance(state: InstanceState) -> None:
    for pid in (state["api_pid"], state["web_pid"]):
        _stop_pid(pid)
    _rmtree(Path(state["instance_dir"]))
    INSTANCE_PATH.unlink(missing_ok=True)


def _stop_pid(pid: int) -> None:
    try:
        os.killpg(pid, signal.SIGTERM)
    except OSError:
        return
    deadline = time.monotonic() + STOP_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        if not _pid_alive(pid):
            return
        time.sleep(0.1)
    try:
        os.killpg(pid, signal.SIGKILL)
    except OSError:
        return


def _rmtree(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
