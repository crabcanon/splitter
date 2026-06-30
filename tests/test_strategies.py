from models.domain import LoadedDocument
from providers.factory import ProviderBundle
from strategies.base import SplitContext
from models.schemas import SplitterType
from strategies.registry import StrategyRegistry


def context(**kwargs: object) -> SplitContext:
    return SplitContext(
        request_id="test",
        strategy_kwargs=dict(kwargs),
        providers=ProviderBundle(),
    )


def strategy(strategy_type: SplitterType):
    return StrategyRegistry.default().get(strategy_type)


def test_markdown_strategy_splits_by_heading() -> None:
    document = LoadedDocument(
        text="# Intro\n\nHello.\n\n## Details\n\nMore text.",
        metadata={"source_type": "text"},
    )
    nodes = strategy(SplitterType.MARKDOWN).split(document, context())

    assert nodes
    assert any("Intro" in node.text for node in nodes)


def test_json_strategy_emits_path_nodes() -> None:
    document = LoadedDocument(
        text='{"user": {"name": "Ada", "active": true}}',
        metadata={"source_type": "text"},
    )
    nodes = strategy(SplitterType.JSON).split(document, context())

    assert nodes
    assert any("Ada" in node.text for node in nodes)


def test_token_strategy_applies_overlap() -> None:
    document = LoadedDocument(text="one two three four five", metadata={})
    nodes = strategy(SplitterType.TOKEN).split(
        document,
        context(chunk_size=3, chunk_overlap=1),
    )

    assert nodes
    assert "one" in nodes[0].text


def test_hierarchical_strategy_adds_parent_child_relationships() -> None:
    document = LoadedDocument(text="alpha beta gamma delta epsilon zeta", metadata={})
    nodes = strategy(SplitterType.HIERARCHICAL).split(
        document,
        context(parent_chunk_size=40, child_chunk_size=12, child_chunk_overlap=0),
    )

    assert nodes
    assert any(node.relationships for node in nodes)
