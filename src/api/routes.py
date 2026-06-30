from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Body, Depends, Request

from core.config import Settings
from models.schemas import HealthResponse, SplitRequest, SplitResponse, StrategiesResponse
from providers.factory import ProviderFactory
from services.orchestrator import SplitOrchestrator
from strategies.registry import StrategyRegistry


router = APIRouter()
_settings = Settings.from_env()
_registry = StrategyRegistry.default()
_orchestrator = SplitOrchestrator(
    settings=_settings,
    strategy_registry=_registry,
    provider_factory=ProviderFactory(_settings),
)

SPLIT_REQUEST_EXAMPLES = {
    "simpleFile": {
        "summary": "SimpleFileNodeParser",
        "description": "通用纯文本内容解析。",
        "value": {
            "content": "Project notes\n\nGoal: simplify the split API.\n\nOutcome: return standard nodes.",
            "mode": "SimpleFileNodeParser",
        },
    },
    "html": {
        "summary": "HTMLNodeParser",
        "description": "HTML 文档结构解析。",
        "value": {
            "content": "<html><body><h1>Release Notes</h1><p>Splitter now accepts content and mode.</p></body></html>",
            "mode": "HTMLNodeParser",
        },
    },
    "json": {
        "summary": "JSONNodeParser",
        "description": "JSON 内容解析。",
        "value": {
            "content": '{"service":"splitter","version":"0.1.0","features":["auto","strategy"]}',
            "mode": "JSONNodeParser",
        },
    },
    "markdown": {
        "summary": "MarkdownNodeParser",
        "description": "Markdown 标题与段落解析。",
        "value": {
            "content": "# Intro\n\nSplitter accepts raw content.\n\n## Details\nUse mode to choose a strategy.",
            "mode": "MarkdownNodeParser",
        },
    },
    "code": {
        "summary": "CodeSplitter",
        "description": "Python 代码切分。",
        "value": {
            "content": "from typing import Iterable\n\n\ndef chunks(items: Iterable[str]) -> list[str]:\n    return [item.strip() for item in items if item.strip()]\n",
            "mode": "CodeSplitter",
        },
    },
    "langchain": {
        "summary": "LangchainNodeParser",
        "description": "使用 LangChain RecursiveCharacterTextSplitter。",
        "value": {
            "content": (
                "LangChain compatible splitting is useful for long prose. "
                "This paragraph gives the splitter enough natural language text to produce a reusable node. "
                "A second paragraph explains that recursive splitting tries larger separators first. "
                "A third paragraph keeps the sample long enough to show multiple chunks in Swagger."
            ),
            "mode": "LangchainNodeParser",
        },
    },
    "chunker": {
        "summary": "Chunker",
        "description": "Chonkie 递归切块。",
        "value": {
            "content": (
                "Chunker can split dense documents into recursive chunks. "
                "It walks through delimiter levels and keeps chunks near the configured size. "
                "This sample is intentionally longer so the result is easier to inspect in Swagger. "
                "Each sentence gives the recursive chunker another place to divide the content."
            ),
            "mode": "Chunker",
        },
    },
    "sentence": {
        "summary": "SentenceSplitter",
        "description": "普通自然语言句子切分。",
        "value": {
            "content": (
                "Splitter exposes a compact API. The service chooses or runs a parser. "
                "The response contains normalized nodes. 中文内容也应该按照句号切分。"
                "这第二个中文句子用于验证自然语言切分。最后一个句子让样例更容易产生多个节点。"
            ),
            "mode": "SentenceSplitter",
        },
    },
    "sentenceWindow": {
        "summary": "SentenceWindowNodeParser",
        "description": "带上下文窗口的句子节点。",
        "value": {
            "content": "The first sentence introduces the topic. The second sentence adds supporting context. The third sentence gives a conclusion.",
            "mode": "SentenceWindowNodeParser",
        },
    },
    "semantic": {
        "summary": "SemanticSplitterNodeParser",
        "description": "语义切分；配置 SPLITTER_EMBEDDING_* 时使用真实 embedding，否则使用本地 MockEmbedding 方便验证。",
        "value": {
            "content": (
                "Search systems need coherent chunks for retrieval. "
                "Embedding based splitters can identify topic changes. "
                "Deployment teams also need clear operational docs. "
                "A separate section discusses API examples and local smoke tests."
            ),
            "mode": "SemanticSplitterNodeParser",
        },
    },
    "token": {
        "summary": "TokenTextSplitter",
        "description": "按 token 窗口切分。",
        "value": {
            "content": (
                "one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen "
                "sixteen seventeen eighteen nineteen twenty twenty-one twenty-two twenty-three twenty-four "
                "twenty-five twenty-six twenty-seven twenty-eight twenty-nine thirty"
            ),
            "mode": "TokenTextSplitter",
        },
    },
    "hierarchical": {
        "summary": "HierarchicalNodeParser",
        "description": "生成父子层级节点。",
        "value": {
            "content": "# Architecture\n\nThe API layer validates requests.\n\n## Services\n\nThe orchestrator selects strategies.\n\n## Strategies\n\nAdapters normalize framework nodes.",
            "mode": "HierarchicalNodeParser",
        },
    },
}


def get_orchestrator() -> SplitOrchestrator:
    return _orchestrator


def get_registry() -> StrategyRegistry:
    return _registry


@router.get("/healthz", tags=["Health"], response_model=HealthResponse)
async def healthz() -> HealthResponse:
    return HealthResponse(service=_settings.app_name, version=_settings.app_version)


@router.get("/api/v1/strategies", tags=["Strategies"], response_model=StrategiesResponse)
async def list_strategies(
    registry: StrategyRegistry = Depends(get_registry),
) -> StrategiesResponse:
    return StrategiesResponse(strategies=registry.list_descriptors())


@router.post("/api/v1/split", tags=["Split"], response_model=SplitResponse)
async def split_document(
    request: Request,
    payload: Annotated[
        SplitRequest,
        Body(openapi_examples=SPLIT_REQUEST_EXAMPLES),
    ],
    orchestrator: SplitOrchestrator = Depends(get_orchestrator),
) -> SplitResponse:
    response = await orchestrator.split(payload)
    request.state.request_id = response.request_id
    return response
