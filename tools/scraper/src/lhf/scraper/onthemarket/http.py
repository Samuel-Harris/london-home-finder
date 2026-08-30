from __future__ import annotations

import time
import urllib.error
import urllib.request

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)
REQUEST_TIMEOUT_SECONDS = 30.0
REQUEST_DELAY_SECONDS = 0.4
MAX_ATTEMPTS = 4
RETRY_BACKOFF_SECONDS = 1.0


class EmptyPage(Exception):
    """HTTP 303 with an empty body: pagination / shard exhausted, not an error."""


class FetchError(Exception):
    """Unrecoverable fetch failure after retry policy."""


class NoFollowRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: object,
        code: int,
        msg: str,
        headers: object,
        newurl: str,
    ) -> urllib.request.Request | None:
        del fp, msg, headers, newurl
        if code == 303:
            raise EmptyPage(f"HTTP 303 fetching {req.full_url}")
        raise FetchError(f"HTTP {code} fetching {req.full_url}")


class Fetcher:
    def __init__(self) -> None:
        self._opener: urllib.request.OpenerDirector | None = None
        self._has_requested = False

    def __enter__(self) -> Fetcher:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def close(self) -> None:
        self._opener = None

    def get(self, url: str) -> str:
        last_error: FetchError | None = None
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        for attempt in range(MAX_ATTEMPTS):
            self._sleep_before_attempt(attempt)
            try:
                with self._ensure_opener().open(
                    request, timeout=REQUEST_TIMEOUT_SECONDS
                ) as response:
                    status = _response_status(response)
                    if status >= 500:
                        last_error = FetchError(f"HTTP {status} fetching {url}")
                        continue
                    if status != 200:
                        raise FetchError(f"HTTP {status} fetching {url}")
                    return response.read().decode("utf-8")
            except EmptyPage:
                raise
            except FetchError:
                raise
            except TimeoutError as exc:
                last_error = FetchError(f"timeout fetching {url}")
                last_error.__cause__ = exc
                continue
            except urllib.error.HTTPError as exc:
                if exc.code == 303:
                    raise EmptyPage(f"HTTP 303 fetching {url}") from exc
                if exc.code >= 500:
                    last_error = FetchError(f"HTTP {exc.code} fetching {url}")
                    last_error.__cause__ = exc
                    continue
                raise FetchError(f"HTTP {exc.code} fetching {url}") from exc
            except urllib.error.URLError as exc:
                last_error = FetchError(f"failed fetching {url}")
                last_error.__cause__ = exc
                continue
        if last_error is None:
            raise FetchError(f"failed fetching {url}")
        raise last_error

    def _ensure_opener(self) -> urllib.request.OpenerDirector:
        if self._opener is None:
            self._opener = urllib.request.build_opener(NoFollowRedirects())
        return self._opener

    def _wait(self) -> None:
        if self._has_requested:
            time.sleep(REQUEST_DELAY_SECONDS)
        self._has_requested = True

    def _sleep_before_attempt(self, attempt: int) -> None:
        if attempt == 0:
            self._wait()
            return
        time.sleep(RETRY_BACKOFF_SECONDS * (2 ** (attempt - 1)))


def _response_status(response: object) -> int:
    status = getattr(response, "status", None)
    if isinstance(status, int):
        return status
    getcode = getattr(response, "getcode", None)
    if callable(getcode):
        code = getcode()
        if isinstance(code, int):
            return code
    raise FetchError("response is missing HTTP status")
