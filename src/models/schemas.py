from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator


class SplitterType(str, Enum):
    SIMPLE_FILE = "SimpleFileNodeParser"
    HTML = "HTMLNodeParser"
    JSON = "JSONNodeParser"
    MARKDOWN = "MarkdownNodeParser"
    CODE = "CodeSplitter"
    LANGCHAIN = "LangchainNodeParser"
    CHUNKER = "Chunker"
    SENTENCE = "SentenceSplitter"
    SENTENCE_WINDOW = "SentenceWindowNodeParser"
    SEMANTIC = "SemanticSplitterNodeParser"
    TOKEN = "TokenTextSplitter"
    HIERARCHICAL = "HierarchicalNodeParser"


class ProviderConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider_name: str = Field(min_length=1)
    model_name: str = Field(min_length=1)
    api_key: SecretStr | None = Field(default=None, exclude=True)
    base_url: str | None = None
    options: dict[str, Any] = Field(default_factory=dict)


class SplitRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: str = Field(min_length=1, description="Document content to split.")
    mode: str = Field(
        default="auto",
        description="Use 'auto' for automatic routing, or pass a strategy name.",
    )

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, value: str) -> str:
        normalized = value.strip()
        if normalized == "auto":
            return normalized
        if normalized in SplitterType._value2member_map_:
            return normalized
        supported = ["auto", *(item.value for item in SplitterType)]
        raise ValueError(f"mode must be one of: {', '.join(supported)}")


class StandardNode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    node_id: str
    text: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    relationships: dict[str, Any] = Field(default_factory=dict)
    start_char_idx: int | None = Field(default=None, ge=0)
    end_char_idx: int | None = Field(default=None, ge=0)
    hash: str


class ProviderSummary(BaseModel):
    provider_name: str
    model_name: str
    base_url: str | None = None
    api_key_configured: bool = False


class SplitResponse(BaseModel):
    status: str = "ok"
    request_id: str
    mode_used: str
    strategy_applied: SplitterType
    total_nodes: int
    nodes: list[StandardNode]
    processing_time_ms: float


class StrategyDescriptor(BaseModel):
    name: SplitterType
    family: str
    description: str
    backend: str


class StrategiesResponse(BaseModel):
    strategies: list[StrategyDescriptor]


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str
    version: str
