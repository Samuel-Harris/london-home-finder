from collections.abc import Iterable

from lhf.repository.protocol import Repository


class _MemoryRepository:
    def __init__(self) -> None:
        self._items: list[str] = []

    def upsert(self, drafts: Iterable[str]) -> int:
        draft_list = list(drafts)
        self._items.extend(draft_list)
        return len(draft_list)

    def list_all(self) -> list[str]:
        return list(self._items)


def test_concrete_class_satisfies_repository_protocol() -> None:
    repository: Repository[str, str] = _MemoryRepository()

    assert repository.upsert(["a", "b"]) == 2
    assert repository.list_all() == ["a", "b"]
