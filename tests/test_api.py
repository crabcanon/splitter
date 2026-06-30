from fastapi.testclient import TestClient

from api.routes import get_orchestrator
from app import app
from models.schemas import SplitterType
from services.orchestrator import SplitOrchestrator


client = TestClient(app)


def test_healthz() -> None:
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_list_strategies() -> None:
    response = client.get("/api/v1/strategies")

    assert response.status_code == 200
    names = {item["name"] for item in response.json()["strategies"]}
    assert "MarkdownNodeParser" in names
    assert "HierarchicalNodeParser" in names


def test_split_auto_markdown() -> None:
    response = client.post(
        "/api/v1/split",
        json={
            "content": "# Intro\n\nHello.\n\n## Details\n\nMore.",
            "mode": "auto",
        },
    )

    payload = response.json()
    assert response.status_code == 200
    assert payload["strategy_applied"] == "MarkdownNodeParser"
    assert payload["total_nodes"] == 2
    assert "diagnostics" not in payload


def test_split_specific_token() -> None:
    response = client.post(
        "/api/v1/split",
        json={
            "content": "one two three four five",
            "mode": "TokenTextSplitter",
        },
    )

    payload = response.json()
    assert response.status_code == 200
    assert payload["strategy_applied"] == "TokenTextSplitter"
    assert payload["total_nodes"] >= 1
    assert "one" in payload["nodes"][0]["text"]


def test_split_specific_code_splitter() -> None:
    response = client.post(
        "/api/v1/split",
        json={
            "content": (
                "from typing import Iterable\n\n\n"
                "def chunks(items: Iterable[str]) -> list[str]:\n"
                "    return [item.strip() for item in items if item.strip()]\n"
            ),
            "mode": "CodeSplitter",
        },
    )

    payload = response.json()
    assert response.status_code == 200
    assert payload["strategy_applied"] == "CodeSplitter"
    assert payload["total_nodes"] >= 1
    assert "def chunks" in payload["nodes"][0]["text"]


def test_sentence_splitter_splits_chinese_natural_language() -> None:
    content = (
        "现在我要基于llamaindex和langchain提供的不同的文本splitter解析器，"
        "开发一个基于fastapi / uv项目工程的API，该工程下的split api，入参只保留文档内容和模式。"
        "请使用优雅的代码模型，分层解耦，使用相关设计模式如策略模式等，提供强大的可扩展性和维护性。"
        "请给出一个完整的技术设计文档，要求有代码模型、设计模式、API设计文档、数据模型和时序图。"
        "要求完整，注意整体工程化的高内聚低耦合和代码质量。"
    )
    response = client.post(
        "/api/v1/split",
        json={"content": content, "mode": "SentenceSplitter"},
    )

    payload = response.json()
    assert response.status_code == 200
    assert payload["strategy_applied"] == "SentenceSplitter"
    assert payload["total_nodes"] > 1
    assert payload["nodes"][0]["text"] != content


def test_split_rejects_old_source_payload() -> None:
    response = client.post(
        "/api/v1/split",
        json={
            "source": {
                "type": "text",
                "content": "# Intro\n\nHello.",
            },
            "mode": "auto",
        },
    )

    assert response.status_code == 422


def test_split_rejects_strategy_kwargs() -> None:
    response = client.post(
        "/api/v1/split",
        json={
            "content": "one two three four five",
            "mode": "TokenTextSplitter",
            "strategy_kwargs": {"chunk_size": 128},
        },
    )

    assert response.status_code == 422


def test_split_openapi_has_strategy_examples_without_diagnostics() -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    spec = response.json()
    split_operation = spec["paths"]["/api/v1/split"]["post"]
    examples = split_operation["requestBody"]["content"]["application/json"]["examples"]
    modes = {example["value"]["mode"] for example in examples.values()}

    assert len(examples) == len(SplitterType)
    assert modes == {strategy.value for strategy in SplitterType}
    split_response = spec["components"]["schemas"]["SplitResponse"]
    assert "diagnostics" not in split_response["properties"]
    assert "diagnostics" not in split_response["required"]


def test_all_swagger_strategy_examples_execute_with_mock_embedding(monkeypatch) -> None:
    monkeypatch.setenv("SPLITTER_EMBEDDING_PROVIDER", "mock")
    monkeypatch.setenv("SPLITTER_EMBEDDING_MODEL", "mock-embedding")
    monkeypatch.delenv("SPLITTER_EMBEDDING_API_KEY", raising=False)
    app.dependency_overrides[get_orchestrator] = lambda: SplitOrchestrator()
    try:
        spec = client.get("/openapi.json").json()
        examples = spec["paths"]["/api/v1/split"]["post"]["requestBody"]["content"][
            "application/json"
        ]["examples"]

        for example in examples.values():
            response = client.post("/api/v1/split", json=example["value"])
            payload = response.json()
            assert response.status_code == 200, payload
            assert payload["strategy_applied"] == example["value"]["mode"]
            assert payload["total_nodes"] >= 1
    finally:
        app.dependency_overrides.pop(get_orchestrator, None)
