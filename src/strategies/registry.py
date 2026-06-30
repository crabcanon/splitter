from __future__ import annotations

from collections.abc import Iterable

from core.errors import UnsupportedStrategyError
from models.schemas import StrategyDescriptor, SplitterType
from strategies.base import BaseSplitterStrategy
from strategies.framework import FrameworkSplitterStrategy, build_strategy_specs


class StrategyRegistry:
    def __init__(self, strategies: Iterable[BaseSplitterStrategy]) -> None:
        self._strategies = {strategy.name: strategy for strategy in strategies}

    @classmethod
    def default(cls) -> "StrategyRegistry":
        return cls(FrameworkSplitterStrategy(spec) for spec in build_strategy_specs())

    def get(self, strategy_type: SplitterType) -> BaseSplitterStrategy:
        try:
            return self._strategies[strategy_type]
        except KeyError as exc:
            raise UnsupportedStrategyError(
                f"Strategy is not registered: {strategy_type.value}"
            ) from exc

    def list_descriptors(self) -> list[StrategyDescriptor]:
        return [strategy.descriptor() for strategy in self._strategies.values()]
