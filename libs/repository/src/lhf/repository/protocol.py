from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol, TypeVar

DraftT = TypeVar("DraftT", contravariant=True)
EntityT = TypeVar("EntityT")


class Repository(Protocol[DraftT, EntityT]):
    """Upsert drafts and list persisted entities."""

    def upsert(self, drafts: Iterable[DraftT]) -> int:
        """Persist drafts, replacing existing rows on natural-key conflict."""
        ...

    def list_all(self) -> list[EntityT]:
        """Return every persisted entity in stable order."""
        ...
