from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol, TypeVar

DraftT = TypeVar("DraftT", contravariant=True)
EntityT = TypeVar("EntityT")


class Repository(Protocol[DraftT, EntityT]):
    """Replace persisted rows from drafts and list entities."""

    def replace_all(self, drafts: Iterable[DraftT]) -> int:
        """Replace every persisted row with the given drafts in one transaction."""
        ...

    def list_all(self) -> list[EntityT]:
        """Return every persisted entity in stable order."""
        ...
