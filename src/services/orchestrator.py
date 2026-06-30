from __future__ import annotations

import time
import uuid

from core.config import Settings
from models.domain import LoadedDocument
from models.schemas import SplitRequest, SplitResponse, SplitterType
from providers.factory import ProviderBundle, ProviderFactory
from services.auto_router import AutoStrategyRouter
from strategies.base import SplitContext
from strategies.registry import StrategyRegistry


class SplitOrchestrator:
    def __init__(
        self,
        *,
        settings: Settings | None = None,
        strategy_registry: StrategyRegistry | None = None,
        provider_factory: ProviderFactory | None = None,
        auto_router: AutoStrategyRouter | None = None,
    ) -> None:
        self.settings = settings or Settings.from_env()
        self.strategy_registry = strategy_registry or StrategyRegistry.default()
        self.provider_factory = provider_factory or ProviderFactory(self.settings)
        self.auto_router = auto_router or AutoStrategyRouter()

    async def split(self, request: SplitRequest) -> SplitResponse:
        started_at = time.perf_counter()
        request_id = uuid.uuid4().hex
        document = LoadedDocument(
            text=request.content,
            metadata={
                "source_type": "text",
                "byte_length": len(request.content.encode("utf-8")),
            },
        )
        providers = self.provider_factory.build_bundle()
        warnings = list(providers.warnings)

        if request.mode == "auto":
            strategy_type = self.auto_router.choose(
                document,
                has_embedding=_has_real_embedding(providers),
            )
        else:
            strategy_type = SplitterType(request.mode)

        strategy = self.strategy_registry.get(strategy_type)
        context = SplitContext(
            request_id=request_id,
            strategy_kwargs={},
            providers=providers,
            warnings=warnings,
        )
        nodes = strategy.split(document, context)
        elapsed_ms = (time.perf_counter() - started_at) * 1000

        return SplitResponse(
            request_id=request_id,
            mode_used=request.mode,
            strategy_applied=strategy_type,
            total_nodes=len(nodes),
            nodes=nodes,
            processing_time_ms=round(elapsed_ms, 3),
        )


def _has_real_embedding(providers: ProviderBundle) -> bool:
    embedding = providers.embedding
    return embedding is not None and embedding.provider_name not in {"mock", "local", "none"}
