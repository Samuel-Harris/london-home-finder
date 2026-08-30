from __future__ import annotations

import time

from playwright.sync_api import Browser, Page, Playwright, sync_playwright
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

ZOOPLA_ORIGIN = "https://www.zoopla.co.uk"
REQUEST_TIMEOUT_SECONDS = 30.0
REQUEST_DELAY_SECONDS = 0.4
MAX_ATTEMPTS = 4
RETRY_BACKOFF_SECONDS = 1.0
_GOTO_TIMEOUT_MS = int(REQUEST_TIMEOUT_SECONDS * 1000)


class FetchError(Exception):
    def __init__(self, message: str, *, status: int | None = None) -> None:
        super().__init__(message)
        self.status = status


class Fetcher:
    def __init__(self) -> None:
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._page: Page | None = None
        self._has_requested = False

    def __enter__(self) -> Fetcher:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def close(self) -> None:
        browser = self._browser
        playwright = self._playwright
        self._page = None
        self._browser = None
        self._playwright = None
        if browser is not None:
            browser.close()
        if playwright is not None:
            playwright.stop()

    def get(self, url: str) -> str:
        last_error: FetchError | None = None
        for attempt in range(MAX_ATTEMPTS):
            self._sleep_before_attempt(attempt)
            page = self._ensure_page()
            try:
                response = page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=_GOTO_TIMEOUT_MS,
                )
            except PlaywrightTimeoutError as exc:
                last_error = FetchError(f"timeout fetching {url}")
                last_error.__cause__ = exc
                self._reset_page()
                continue
            except PlaywrightError as exc:
                last_error = FetchError(f"failed fetching {url}")
                last_error.__cause__ = exc
                self._reset_page()
                continue
            if response is None:
                raise FetchError(f"no response fetching {url}")
            status = response.status
            if status >= 500:
                last_error = FetchError(f"HTTP {status} fetching {url}", status=status)
                continue
            if status >= 400:
                raise FetchError(f"HTTP {status} fetching {url}", status=status)
            return page.content()
        if last_error is None:
            raise FetchError(f"failed fetching {url}")
        raise last_error

    def _ensure_page(self) -> Page:
        if self._page is not None:
            return self._page
        browser = self._browser
        if browser is None:
            playwright = sync_playwright().start()
            self._playwright = playwright
            try:
                browser = self._launch_browser(playwright)
            except PlaywrightError as exc:
                self.close()
                raise FetchError(
                    "failed to start Chromium; run `uv run playwright install chromium`"
                ) from exc
            self._browser = browser
        try:
            page = browser.new_page()
        except PlaywrightError as exc:
            self.close()
            raise FetchError(
                "failed to start Chromium; run `uv run playwright install chromium`"
            ) from exc
        self._page = page
        return page

    def _reset_page(self) -> None:
        page = self._page
        self._page = None
        if page is None:
            return
        try:
            page.close()
        except PlaywrightError:
            return

    def _launch_browser(self, playwright: Playwright) -> Browser:
        try:
            return playwright.chromium.launch(channel="chrome", headless=True)
        except PlaywrightError:
            return playwright.chromium.launch(headless=True)

    def _wait(self) -> None:
        if self._has_requested:
            time.sleep(REQUEST_DELAY_SECONDS)
        self._has_requested = True

    def _sleep_before_attempt(self, attempt: int) -> None:
        if attempt == 0:
            self._wait()
            return
        time.sleep(RETRY_BACKOFF_SECONDS * (2 ** (attempt - 1)))
