from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Any, Callable

from core.errors import StrategyExecutionError
from models.domain import LoadedDocument
from models.schemas import StandardNode, SplitterType
from strategies.base import BaseSplitterStrategy, SplitContext


ParserBuilder = Callable[[SplitContext], Any]
NATURAL_CHUNK_SIZE = 128
NATURAL_CHUNK_OVERLAP = 20
CHAR_CHUNK_SIZE = 240
CHAR_CHUNK_OVERLAP = 32


@dataclass(frozen=True)
class FrameworkStrategySpec:
    name: SplitterType
    family: str
    description: str
    backend: str
    builder: ParserBuilder
    default_kwargs: dict[str, Any] = field(default_factory=dict)


class FrameworkSplitterStrategy(BaseSplitterStrategy):
    """Thin adapter around parser implementations supplied by LlamaIndex/LangChain."""

    def __init__(self, spec: FrameworkStrategySpec) -> None:
        self.name = spec.name
        self.family = spec.family
        self.description = spec.description
        self.backend = spec.backend
        self._builder = spec.builder
        self._default_kwargs = spec.default_kwargs

    def split(self, document: LoadedDocument, context: SplitContext) -> list[StandardNode]:
        try:
            parser = self._builder(_context_with_defaults(context, self._default_kwargs))
            nodes = parser.get_nodes_from_documents([_document(document)])
        except Exception as exc:
            raise StrategyExecutionError(
                f"{self.name.value} failed in {self.backend} backend: {exc}"
            ) from exc
        return standardize_nodes(nodes, document.metadata)


def build_strategy_specs() -> list[FrameworkStrategySpec]:
    return [
        FrameworkStrategySpec(
            name=SplitterType.SIMPLE_FILE,
            family="File-Based Node Parsers",
            description="LlamaIndex SimpleFileNodeParser for general file documents.",
            backend="llamaindex",
            builder=_simple_file_parser,
        ),
        FrameworkStrategySpec(
            name=SplitterType.HTML,
            family="File-Based Node Parsers",
            description="LlamaIndex HTMLNodeParser.",
            backend="llamaindex",
            builder=_node_parser_builder("HTMLNodeParser"),
        ),
        FrameworkStrategySpec(
            name=SplitterType.JSON,
            family="File-Based Node Parsers",
            description="LlamaIndex JSONNodeParser.",
            backend="llamaindex",
            builder=_node_parser_builder("JSONNodeParser"),
        ),
        FrameworkStrategySpec(
            name=SplitterType.MARKDOWN,
            family="File-Based Node Parsers",
            description="LlamaIndex MarkdownNodeParser.",
            backend="llamaindex",
            builder=_node_parser_builder("MarkdownNodeParser"),
        ),
        FrameworkStrategySpec(
            name=SplitterType.CODE,
            family="Text-Splitters",
            description="LlamaIndex CodeSplitter.",
            backend="llamaindex",
            builder=_code_splitter,
            default_kwargs={"language": "python"},
        ),
        FrameworkStrategySpec(
            name=SplitterType.LANGCHAIN,
            family="Text-Splitters",
            description="LlamaIndex LangchainNodeParser wrapping RecursiveCharacterTextSplitter.",
            backend="llamaindex+langchain",
            builder=_langchain_node_parser,
            default_kwargs={
                "chunk_size": CHAR_CHUNK_SIZE,
                "chunk_overlap": CHAR_CHUNK_OVERLAP,
            },
        ),
        FrameworkStrategySpec(
            name=SplitterType.CHUNKER,
            family="Text-Splitters",
            description="Chonkie RecursiveChunker adapter.",
            backend="chonkie",
            builder=_chonkie_chunker,
            default_kwargs={
                "recursive_kwargs": {
                    "chunk_size": CHAR_CHUNK_SIZE,
                    "min_characters_per_chunk": 24,
                }
            },
        ),
        FrameworkStrategySpec(
            name=SplitterType.SENTENCE,
            family="Text-Splitters",
            description="LlamaIndex SentenceSplitter.",
            backend="llamaindex",
            builder=_node_parser_builder("SentenceSplitter"),
            default_kwargs={
                "chunk_size": NATURAL_CHUNK_SIZE,
                "chunk_overlap": NATURAL_CHUNK_OVERLAP,
            },
        ),
        FrameworkStrategySpec(
            name=SplitterType.SENTENCE_WINDOW,
            family="Text-Splitters",
            description="LlamaIndex SentenceWindowNodeParser.",
            backend="llamaindex",
            builder=_node_parser_builder("SentenceWindowNodeParser"),
            default_kwargs={
                "sentence_splitter": _split_sentences,
                "window_size": 3,
            },
        ),
        FrameworkStrategySpec(
            name=SplitterType.SEMANTIC,
            family="Text-Splitters",
            description="LlamaIndex SemanticSplitterNodeParser with configured embedding model.",
            backend="llamaindex",
            builder=_semantic_splitter,
            default_kwargs={
                "sentence_splitter": _split_sentences,
            },
        ),
        FrameworkStrategySpec(
            name=SplitterType.TOKEN,
            family="Text-Splitters",
            description="LlamaIndex TokenTextSplitter.",
            backend="llamaindex",
            builder=_node_parser_builder("TokenTextSplitter"),
            default_kwargs={
                "chunk_size": NATURAL_CHUNK_SIZE,
                "chunk_overlap": NATURAL_CHUNK_OVERLAP,
                "include_metadata": False,
            },
        ),
        FrameworkStrategySpec(
            name=SplitterType.HIERARCHICAL,
            family="Relation-Based Node Parsers",
            description="LlamaIndex HierarchicalNodeParser.",
            backend="llamaindex",
            builder=_hierarchical_parser,
            default_kwargs={
                "chunk_sizes": [256, 128],
                "chunk_overlap": NATURAL_CHUNK_OVERLAP,
            },
        ),
    ]


def _document(document: LoadedDocument) -> Any:
    from llama_index.core import Document

    # Keep framework chunk sizing independent from API metadata length; metadata is
    # merged back into StandardNode after the parser returns.
    return Document(text=document.text, metadata={})


def _simple_file_parser(context: SplitContext) -> Any:
    from llama_index.core.node_parser import SimpleFileNodeParser

    return _instantiate(SimpleFileNodeParser, _parser_kwargs(context))


def _node_parser_builder(class_name: str) -> ParserBuilder:
    def build(context: SplitContext) -> Any:
        from llama_index.core import node_parser

        parser_cls = getattr(node_parser, class_name)
        return _instantiate(parser_cls, _parser_kwargs(context))

    return build


def _langchain_node_parser(context: SplitContext) -> Any:
    from llama_index.core.node_parser import LangchainNodeParser
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    kwargs = _parser_kwargs(context)
    splitter_kwargs = kwargs.pop("splitter_kwargs", {})
    splitter_kwargs.setdefault("chunk_size", kwargs.pop("chunk_size", 1000))
    splitter_kwargs.setdefault("chunk_overlap", kwargs.pop("chunk_overlap", 100))
    splitter = RecursiveCharacterTextSplitter(**splitter_kwargs)
    return LangchainNodeParser(splitter, **kwargs)


def _code_splitter(context: SplitContext) -> Any:
    from llama_index.core.node_parser import CodeSplitter

    kwargs = _parser_kwargs(context)
    if "parser" not in kwargs:
        language = str(kwargs.get("language", "python"))
        try:
            import tree_sitter_language_pack
        except ImportError as exc:
            raise StrategyExecutionError(
                "CodeSplitter requires tree-sitter-language-pack."
            ) from exc
        kwargs["parser"] = _CodeParserAdapter(
            tree_sitter_language_pack.get_parser(language)
        )
    return _instantiate(CodeSplitter, kwargs)


class _CodeParserAdapter:
    """Bridge LlamaIndex CodeSplitter bytes input to language-pack parser APIs."""

    def __init__(self, parser: Any) -> None:
        self._parser = parser

    def parse(self, payload: Any) -> Any:
        try:
            return _CodeTreeAdapter(self._parser.parse(payload))
        except TypeError:
            if isinstance(payload, (bytes, bytearray)):
                return _CodeTreeAdapter(
                    self._parser.parse(bytes(payload).decode("utf-8"))
                )
            if isinstance(payload, str):
                return _CodeTreeAdapter(self._parser.parse(payload.encode("utf-8")))
            raise


class _CodeTreeAdapter:
    def __init__(self, tree: Any) -> None:
        self._tree = tree

    @property
    def root_node(self) -> Any:
        root_node = _value(getattr(self._tree, "root_node"))
        return _CodeNodeAdapter(root_node)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._tree, name)


class _CodeNodeAdapter:
    def __init__(self, node: Any) -> None:
        self._node = node

    @property
    def type(self) -> str:
        return str(_value(getattr(self._node, "type", None) or getattr(self._node, "kind")))

    @property
    def children(self) -> list[Any]:
        direct_children = getattr(self._node, "children", None)
        if direct_children is not None:
            return [_CodeNodeAdapter(child) for child in _value(direct_children)]

        child_count = int(_value(getattr(self._node, "child_count", 0)))
        child = getattr(self._node, "child")
        return [_CodeNodeAdapter(child(index)) for index in range(child_count)]

    @property
    def start_byte(self) -> int:
        return int(_value(getattr(self._node, "start_byte")))

    @property
    def end_byte(self) -> int:
        return int(_value(getattr(self._node, "end_byte")))

    def __getattr__(self, name: str) -> Any:
        return getattr(self._node, name)


def _value(value: Any) -> Any:
    if callable(value):
        return value()
    return value


def _chonkie_chunker(context: SplitContext) -> Any:
    from chonkie import RecursiveChunker

    kwargs = _parser_kwargs(context)
    recursive_kwargs = kwargs.pop("recursive_kwargs", {})
    return _ChonkieParserAdapter(RecursiveChunker(**recursive_kwargs))


class _ChonkieParserAdapter:
    """Expose Chonkie chunks through the parser interface used by strategies."""

    def __init__(self, chunker: Any) -> None:
        self._chunker = chunker

    def get_nodes_from_documents(self, documents: list[Any]) -> list[Any]:
        nodes: list[Any] = []
        for document_index, document in enumerate(documents, start=1):
            text = str(getattr(document, "text", "") or "")
            for chunk_index, chunk in enumerate(self._chunker.chunk(text), start=1):
                nodes.append(
                    _ChonkieNodeAdapter(
                        chunk=chunk,
                        document_index=document_index,
                        chunk_index=chunk_index,
                    )
                )
        return nodes


class _ChonkieNodeAdapter:
    def __init__(self, chunk: Any, document_index: int, chunk_index: int) -> None:
        self._chunk = chunk
        self._document_index = document_index
        self._chunk_index = chunk_index

    @property
    def node_id(self) -> str:
        start = self.start_char_idx
        end = self.end_char_idx
        return f"chonkie_{self._document_index}_{self._chunk_index}_{start}_{end}"

    @property
    def metadata(self) -> dict[str, Any]:
        token_count = getattr(self._chunk, "token_count", None)
        if token_count is None:
            return {}
        return {"token_count": int(token_count)}

    @property
    def relationships(self) -> dict[str, Any]:
        return {}

    @property
    def start_char_idx(self) -> int | None:
        return _optional_int(getattr(self._chunk, "start_index", None))

    @property
    def end_char_idx(self) -> int | None:
        return _optional_int(getattr(self._chunk, "end_index", None))

    def get_content(self) -> str:
        return str(getattr(self._chunk, "text", "") or "")


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)


def _semantic_splitter(context: SplitContext) -> Any:
    from llama_index.core.node_parser import SemanticSplitterNodeParser

    kwargs = _parser_kwargs(context)
    kwargs.setdefault("embed_model", _embedding_model(context))
    return SemanticSplitterNodeParser(**kwargs)


def _hierarchical_parser(context: SplitContext) -> Any:
    from llama_index.core.node_parser import HierarchicalNodeParser

    kwargs = _parser_kwargs(context)
    parent_chunk_size = kwargs.pop("parent_chunk_size", None)
    child_chunk_size = kwargs.pop("child_chunk_size", None)
    child_chunk_overlap = kwargs.pop("child_chunk_overlap", None)

    if "chunk_sizes" not in kwargs and (
        parent_chunk_size is not None or child_chunk_size is not None
    ):
        chunk_sizes = [
            int(size)
            for size in (parent_chunk_size, child_chunk_size)
            if size is not None
        ]
        if chunk_sizes:
            kwargs["chunk_sizes"] = chunk_sizes

    if child_chunk_overlap is not None and "chunk_overlap" not in kwargs:
        kwargs["chunk_overlap"] = int(child_chunk_overlap)

    return HierarchicalNodeParser.from_defaults(**kwargs)


def _embedding_model(context: SplitContext) -> Any:
    from llama_index.core.embeddings import MockEmbedding
    from llama_index.embeddings.openai import OpenAIEmbedding

    provider = context.providers.embedding
    if provider is None:
        return MockEmbedding(embed_dim=384)

    if provider.provider_name in {"mock", "local", "none"}:
        embed_dim = int(provider.options.get("embed_dim", 384))
        return MockEmbedding(embed_dim=embed_dim)

    kwargs: dict[str, Any] = {"model": provider.model_name}
    if provider.api_key is not None:
        kwargs["api_key"] = provider.api_key.get_secret_value()
    if provider.base_url:
        kwargs["api_base"] = provider.base_url
    kwargs.update(provider.options)
    return OpenAIEmbedding(**kwargs)


def _split_sentences(text: str) -> list[str]:
    normalized = text.strip()
    if not normalized:
        return []

    matches = re.finditer(
        r".+?(?:[。！？；;!?]+|\.(?=\s|$)|\n+|$)",
        normalized,
        flags=re.S,
    )
    sentences = [match.group(0).strip() for match in matches if match.group(0).strip()]
    return sentences or [normalized]


def _context_with_defaults(
    context: SplitContext,
    defaults: dict[str, Any],
) -> SplitContext:
    if not defaults:
        return context
    strategy_kwargs = dict(defaults)
    strategy_kwargs.update(context.strategy_kwargs)
    return SplitContext(
        request_id=context.request_id,
        strategy_kwargs=strategy_kwargs,
        providers=context.providers,
        warnings=context.warnings,
    )


def _parser_kwargs(context: SplitContext) -> dict[str, Any]:
    ignored = {
        "backend",
        "framework",
        "llamaindex_kwargs",
        "langchain_kwargs",
        "chonkie_kwargs",
    }
    kwargs = {
        key: value
        for key, value in context.strategy_kwargs.items()
        if key not in ignored and value is not None
    }
    kwargs.update(context.strategy_kwargs.get("llamaindex_kwargs", {}))
    return kwargs


def _instantiate(parser_cls: type[Any], kwargs: dict[str, Any]) -> Any:
    if hasattr(parser_cls, "from_defaults"):
        return parser_cls.from_defaults(**kwargs)
    return parser_cls(**kwargs)


def standardize_nodes(
    nodes: list[Any],
    base_metadata: dict[str, Any],
) -> list[StandardNode]:
    standard_nodes: list[StandardNode] = []
    for index, node in enumerate(nodes, start=1):
        text = _node_text(node)
        metadata = dict(base_metadata)
        metadata.update(getattr(node, "metadata", {}) or {})
        standard_nodes.append(
            StandardNode(
                node_id=str(getattr(node, "node_id", None) or f"node_{index:04d}"),
                text=text,
                metadata=metadata,
                relationships=_relationships(node),
                start_char_idx=getattr(node, "start_char_idx", None),
                end_char_idx=getattr(node, "end_char_idx", None),
                hash=hashlib.sha256(text.encode("utf-8")).hexdigest(),
            )
        )
    return standard_nodes


def _node_text(node: Any) -> str:
    if hasattr(node, "get_content"):
        return str(node.get_content())
    return str(getattr(node, "text", ""))


def _relationships(node: Any) -> dict[str, Any]:
    raw = getattr(node, "relationships", {}) or {}
    return {str(key): _relationship_value(value) for key, value in raw.items()}


def _relationship_value(value: Any) -> Any:
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, tuple):
        return [str(item) for item in value]
    return str(value)
