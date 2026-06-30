from __future__ import annotations

from typing import Protocol

from models.domain import LoadedDocument
from models.schemas import StandardNode


class SplitterStrategyProtocol(Protocol):
    def split(self, document: LoadedDocument, context: object) -> list[StandardNode]:
        """Split a loaded document into standard API nodes."""
