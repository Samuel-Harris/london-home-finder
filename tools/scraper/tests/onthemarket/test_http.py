from __future__ import annotations

from email.message import Message
from io import BytesIO
from urllib.error import HTTPError
from urllib.request import Request

import pytest
from lhf.scraper.onthemarket.http import EmptyPage, Fetcher, FetchError, NoFollowRedirects

_SEARCH_URL = "https://www.onthemarket.com/for-sale/2-bed-houses/london/?page=35"


class _FakeResponse:
    def __init__(self, status: int, body: bytes = b"<html>ok</html>") -> None:
        self.status = status
        self.code = status
        self.msg = "OK"
        self._body = body
        self.headers = Message()

    def read(self) -> bytes:
        return self._body

    def getcode(self) -> int:
        return self.code

    def info(self) -> Message:
        return self.headers

    def close(self) -> None:
        return None

    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(self, *_exc: object) -> None:
        return None


class _FakeOpener:
    def __init__(self, outcomes: list[object]) -> None:
        self.outcomes = list(outcomes)
        self.urls: list[str] = []

    def open(self, req: Request, timeout: float | None = None) -> _FakeResponse:
        del timeout
        self.urls.append(req.full_url)
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        if isinstance(outcome, _FakeResponse):
            return outcome
        raise TypeError("unexpected fake opener outcome")


def test_303_is_empty_page_without_following() -> None:
    handler = NoFollowRedirects()
    req = Request(_SEARCH_URL)
    headers = Message()
    headers["Location"] = "https://www.onthemarket.com/for-sale/2-bed-houses/london/?page=36"
    with pytest.raises(EmptyPage, match="HTTP 303"):
        handler.redirect_request(
            req, BytesIO(b"followed-body"), 303, "See Other", headers, headers["Location"]
        )


def test_other_redirects_are_fetch_errors() -> None:
    handler = NoFollowRedirects()
    req = Request(_SEARCH_URL)
    headers = Message()
    headers["Location"] = "https://www.onthemarket.com/elsewhere/"
    with pytest.raises(FetchError, match="HTTP 302"):
        handler.redirect_request(req, BytesIO(b""), 302, "Found", headers, headers["Location"])


def test_get_returns_200_html(monkeypatch: pytest.MonkeyPatch) -> None:
    opener = _FakeOpener([_FakeResponse(200, b"<html>listings</html>")])
    fetcher = Fetcher()
    monkeypatch.setattr(fetcher, "_ensure_opener", lambda: opener)
    monkeypatch.setattr(fetcher, "_wait", lambda: None)

    assert fetcher.get(_SEARCH_URL) == "<html>listings</html>"
    assert opener.urls == [_SEARCH_URL]


def test_get_treats_http_error_303_as_empty_page(monkeypatch: pytest.MonkeyPatch) -> None:
    error = HTTPError(_SEARCH_URL, 303, "See Other", Message(), BytesIO(b""))
    opener = _FakeOpener([error, _FakeResponse(200)])
    fetcher = Fetcher()
    monkeypatch.setattr(fetcher, "_ensure_opener", lambda: opener)
    monkeypatch.setattr(fetcher, "_wait", lambda: None)

    with pytest.raises(EmptyPage, match="HTTP 303"):
        fetcher.get(_SEARCH_URL)
    assert opener.urls == [_SEARCH_URL]


def test_get_raises_immediately_on_404(monkeypatch: pytest.MonkeyPatch) -> None:
    error = HTTPError(_SEARCH_URL, 404, "Not Found", Message(), BytesIO(b""))
    opener = _FakeOpener([error, _FakeResponse(200)])
    fetcher = Fetcher()
    sleeps: list[float] = []
    monkeypatch.setattr("lhf.scraper.onthemarket.http.time.sleep", sleeps.append)
    monkeypatch.setattr(fetcher, "_ensure_opener", lambda: opener)
    monkeypatch.setattr(fetcher, "_wait", lambda: None)

    with pytest.raises(FetchError, match="HTTP 404"):
        fetcher.get(_SEARCH_URL)
    assert opener.urls == [_SEARCH_URL]
    assert sleeps == []


def test_get_retries_server_errors_with_backoff(monkeypatch: pytest.MonkeyPatch) -> None:
    opener = _FakeOpener(
        [
            HTTPError(_SEARCH_URL, 503, "Unavailable", Message(), BytesIO(b"")),
            _FakeResponse(200, b"<html>ok</html>"),
        ]
    )
    fetcher = Fetcher()
    sleeps: list[float] = []
    monkeypatch.setattr("lhf.scraper.onthemarket.http.time.sleep", sleeps.append)
    monkeypatch.setattr(fetcher, "_ensure_opener", lambda: opener)
    monkeypatch.setattr(fetcher, "_wait", lambda: None)

    assert fetcher.get(_SEARCH_URL) == "<html>ok</html>"
    assert len(opener.urls) == 2
    assert sleeps == [1.0]
