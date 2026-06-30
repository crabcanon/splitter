from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from models.domain import LoadedDocument
from models.schemas import StandardNode, StrategyDescriptor, SplitterType
from providers.factory import ProviderBundle


@dataclass
class SplitContext:
    request_id: str
    strategy_kwargs: dict[str, Any]
    providers: ProviderBundle
    warnings: list[str] = field(default_factory=list)


class BaseSplitterStrategy:
    name: SplitterType
    family: str
    description: str
    backend = "llamaindex"

    def descriptor(self) -> StrategyDescriptor:
        return StrategyDescriptor(
            name=self.name,
            family=self.family,
            description=self.description,
            backend=self.backend,
        )

    def split(self, document: LoadedDocument, context: SplitContext) -> list[StandardNode]:
        raise NotImplementedError
