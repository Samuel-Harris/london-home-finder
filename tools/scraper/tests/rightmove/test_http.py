import pytest
from lhf.scraper.rightmove.http import Fetcher, FetchError
from playwright.sync_api import Error as PlaywrightError

_INTERRUPTED = (
    'Page.goto: Navigation is interrupted by another navigation to "chrome-error://chromewebdata/"'
)
_SEARCH_URL = "https://www.rightmove.co.uk/property-for-sale/find.html"


class _FakeResponse:
    def __init__(self, status: int) -> None:
        self.status = status


class _FakePage:
    def __init__(self, outcomes: list[int | PlaywrightError]) -> None:
        self.outcomes = outcomes
        self.gotos = 0

    def goto(self, url: str, wait_until: str, timeout: float) -> _FakeResponse:
        del url, wait_until, timeout
        outcome = self.outcomes[self.gotos]
        self.gotos += 1
        if isinstance(outcome, PlaywrightError):
            raise outcome
        return _FakeResponse(outcome)

    def content(self) -> str:
        return "<html>ok</html>"


def _patch_fetcher(
    monkeypatch: pytest.MonkeyPatch, fetcher: Fetcher, page: _FakePage
) -> list[float]:
    sleeps: list[float] = []
    monkeypatch.setattr("lhf.scraper.rightmove.http.time.sleep", sleeps.append)
    monkeypatch.setattr(fetcher, "_wait", lambda: None)
    monkeypatch.setattr(fetcher, "_ensure_page", lambda: page)
    monkeypatch.setattr(fetcher, "_reset_page", lambda: None)
    return sleeps


def test_get_retries_interrupted_navigation_with_backoff(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    page = _FakePage([PlaywrightError(_INTERRUPTED), 200])
    fetcher = Fetcher()
    resets: list[int] = []
    sleeps = _patch_fetcher(monkeypatch, fetcher, page)
    monkeypatch.setattr(fetcher, "_reset_page", lambda: resets.append(1))

    assert fetcher.get(_SEARCH_URL) == "<html>ok</html>"
    assert page.gotos == 2
    assert resets == [1]
    assert sleeps == [1.0]


def test_get_raises_after_backoff_retries_are_exhausted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    error = PlaywrightError(_INTERRUPTED)
    page = _FakePage([error, error, error, error])
    fetcher = Fetcher()
    sleeps = _patch_fetcher(monkeypatch, fetcher, page)

    with pytest.raises(FetchError, match="failed fetching"):
        fetcher.get(_SEARCH_URL)
    assert page.gotos == 4
    assert sleeps == [1.0, 2.0, 4.0]


def test_get_retries_server_errors_with_backoff(monkeypatch: pytest.MonkeyPatch) -> None:
    page = _FakePage([503, 200])
    fetcher = Fetcher()
    sleeps = _patch_fetcher(monkeypatch, fetcher, page)

    assert fetcher.get(_SEARCH_URL) == "<html>ok</html>"
    assert page.gotos == 2
    assert sleeps == [1.0]
