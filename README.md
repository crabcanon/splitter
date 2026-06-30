# Splitter

基于 FastAPI、uv、LlamaIndex、LangChain 与 Chonkie 的文档内容解析与切分服务。

当前 `/api/v1/split` 接口已简化为只接收两个字段：

- `content`：待切分的文档内容。
- `mode`：`auto` 或任一注册策略名称，例如 `MarkdownNodeParser`、`TokenTextSplitter`。

服务不再支持文件上传、base64 文件内容或 URL 文件地址输入。LLM 与 Embedding Provider 通过 `.env` 或环境变量配置，不再从请求体传入。

## 快速启动

```bash
uv sync --extra dev
uv run uvicorn app:app --app-dir src --reload
```

健康检查：

```bash
curl http://127.0.0.1:8000/healthz
```

切分示例：

```bash
curl -X POST http://127.0.0.1:8000/api/v1/split \
  -H 'Content-Type: application/json' \
  -d '{
    "content": "# Intro\n\nHello splitter.\n\n## Details\nMore content.",
    "mode": "auto"
  }'
```

指定策略：

```bash
curl -X POST http://127.0.0.1:8000/api/v1/split \
  -H 'Content-Type: application/json' \
  -d '{
    "content": "A long document that should be split by token windows.",
    "mode": "TokenTextSplitter"
  }'
```

## 支持策略

| Family | Strategy | Backend |
|---|---|---|
| File-Based | `SimpleFileNodeParser` | LlamaIndex |
| File-Based | `HTMLNodeParser` | LlamaIndex |
| File-Based | `JSONNodeParser` | LlamaIndex |
| File-Based | `MarkdownNodeParser` | LlamaIndex |
| Text-Splitters | `CodeSplitter` | LlamaIndex |
| Text-Splitters | `LangchainNodeParser` | LlamaIndex + LangChain |
| Text-Splitters | `Chunker` | LlamaIndex + Chonkie |
| Text-Splitters | `SentenceSplitter` | LlamaIndex |
| Text-Splitters | `SentenceWindowNodeParser` | LlamaIndex |
| Text-Splitters | `SemanticSplitterNodeParser` | LlamaIndex + OpenAIEmbedding |
| Text-Splitters | `TokenTextSplitter` | LlamaIndex |
| Relation-Based | `HierarchicalNodeParser` | LlamaIndex |

所有策略均直接使用底层框架已实现的 parser/splitter，本项目只负责请求模型、provider 配置、parser 构造和 `StandardNode` 响应标准化。

## 环境配置

复制 `.env.example` 后按需填写：

```bash
cp .env.example .env
```

常用变量：

```env
SPLITTER_LLM_PROVIDER=openai
SPLITTER_LLM_MODEL=gpt-4.1-mini
SPLITTER_LLM_BASE_URL=https://api.openai.com/v1
SPLITTER_LLM_API_KEY=

SPLITTER_EMBEDDING_PROVIDER=
SPLITTER_EMBEDDING_MODEL=
SPLITTER_EMBEDDING_BASE_URL=
SPLITTER_EMBEDDING_API_KEY=
```

如果需要真实语义切分，可配置 OpenAI 兼容 embedding：

```env
SPLITTER_EMBEDDING_PROVIDER=openai
SPLITTER_EMBEDDING_MODEL=text-embedding-3-small
SPLITTER_EMBEDDING_BASE_URL=https://api.openai.com/v1
SPLITTER_EMBEDDING_API_KEY=sk-...
```

## Docker Compose

```bash
docker compose up -d --build
```

## 文档

- 详细设计：[docs/technical-design.md](docs/technical-design.md)
- API 设计：[docs/api-design.md](docs/api-design.md)
- OpenAPI 3.1.0：[docs/openapi.yaml](docs/openapi.yaml)
- 部署方案：[docs/deployment.md](docs/deployment.md)
- 实施任务清单：[docs/splitter-tasks.md](docs/splitter-tasks.md)
- 实施问题日志：[docs/splitter-logs.md](docs/splitter-logs.md)

## 验证

```bash
uv run --extra dev pytest
```
