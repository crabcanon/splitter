from models.domain import LoadedDocument
from models.schemas import SplitterType
from services.auto_router import AutoStrategyRouter


def test_auto_router_detects_markdown_content() -> None:
    strategy = AutoStrategyRouter().choose(
        LoadedDocument(text="# Title\n\nBody", metadata={}),
    )

    assert strategy == SplitterType.MARKDOWN


def test_auto_router_detects_json_content() -> None:
    strategy = AutoStrategyRouter().choose(
        LoadedDocument(text='{"name": "splitter"}', metadata={}),
    )

    assert strategy == SplitterType.JSON
