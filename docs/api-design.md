# API 设计文档

本服务以 OpenAPI 3.1.0 作为 API 契约基础，规范文件位于 [`docs/openapi.yaml`](openapi.yaml)。

## 1. API 版本

- Base URL: `/`
- API Prefix: `/api/v1`
- Content-Type: `application/json`
- OpenAPI: `3.1.0`

## 2. Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/healthz` | 健康检查 |
| `GET` | `/api/v1/strategies` | 查询可用切分策略 |
| `POST` | `/api/v1/split` | 执行文档内容解析与切分 |

## 3. POST `/api/v1/split`

### 3.1 请求字段

当前接口只保留两个入参，不再支持文件上传、base64 文件内容或 URL 文件地址。

| Field | Type | Required | Description |
|---|---|---|---|
| `content` | string | yes | 待切分的文档内容，最小长度为 1 |
| `mode` | string | no | `auto` 或任一策略名称；默认 `auto` |

`mode=auto` 时，服务根据内容特征自动选择策略；传入策略名称时直接使用该策略，例如 `MarkdownNodeParser`、`TokenTextSplitter`。

### 3.2 Swagger 请求样例

运行时 Swagger UI 会在 `/api/v1/split` 的 request body 中提供 12 个策略样例：

- `SimpleFileNodeParser`
- `HTMLNodeParser`
- `JSONNodeParser`
- `MarkdownNodeParser`
- `CodeSplitter`
- `LangchainNodeParser`
- `Chunker`
- `SentenceSplitter`
- `SentenceWindowNodeParser`
- `SemanticSplitterNodeParser`
- `TokenTextSplitter`
- `HierarchicalNodeParser`

用户可以直接在 Swagger 中选择样例并执行，无需手动构造请求体。

### 3.3 请求示例：自动路由 Markdown

```json
{
  "content": "# Intro\n\nThis is a document.\n\n## Details\nMore content.",
  "mode": "auto"
}
```

### 3.4 请求示例：指定 TokenTextSplitter

```json
{
  "content": "A long document that should be split by token windows.",
  "mode": "TokenTextSplitter"
}
```

### 3.5 响应示例

```json
{
  "status": "ok",
  "request_id": "25e4ed26d5e942d1a95da783d4f7e4f7",
  "mode_used": "auto",
  "strategy_applied": "MarkdownNodeParser",
  "total_nodes": 2,
  "nodes": [
    {
      "node_id": "node_0001",
      "text": "Intro\n\nThis is a document.",
      "metadata": {
        "source_type": "text",
        "heading": "Intro"
      },
      "relationships": {},
      "start_char_idx": 0,
      "end_char_idx": 27,
      "hash": "..."
    }
  ],
  "processing_time_ms": 2.4
}
```

## 4. 支持策略

| Strategy | Family | Typical Usage |
|---|---|---|
| `SimpleFileNodeParser` | File-Based | 通用纯文本或未知格式内容 |
| `HTMLNodeParser` | File-Based | HTML 内容 |
| `JSONNodeParser` | File-Based | JSON 配置、API 响应、结构化内容 |
| `MarkdownNodeParser` | File-Based | Markdown 内容 |
| `CodeSplitter` | Text-Splitters | 代码或含大量代码结构的内容 |
| `LangchainNodeParser` | Text-Splitters | LangChain 兼容入口 |
| `Chunker` | Text-Splitters | Chonkie 递归切块 |
| `SentenceSplitter` | Text-Splitters | 普通自然语言文本 |
| `SentenceWindowNodeParser` | Text-Splitters | 需要句子上下文窗口的检索场景 |
| `SemanticSplitterNodeParser` | Text-Splitters | 配置 embedding 后使用真实语义切分；未配置时用 MockEmbedding 便于本地验证 |
| `TokenTextSplitter` | Text-Splitters | Token 窗口控制 |
| `HierarchicalNodeParser` | Relation-Based | 需要父子层级节点的检索场景 |

## 5. 错误响应

```json
{
  "error": {
    "code": "UNSUPPORTED_STRATEGY",
    "message": "Strategy is not registered: UnknownSplitter",
    "request_id": "25e4ed26d5e942d1a95da783d4f7e4f7"
  }
}
```

常见错误：

| HTTP Status | Code | Scenario |
|---:|---|---|
| 400 | `UNSUPPORTED_STRATEGY` | `mode` 指定的策略未注册或不可用 |
| 400 | `STRATEGY_EXECUTION_ERROR` | 底层 parser 构造或执行失败 |
| 422 | FastAPI validation | 请求字段缺失、字段类型错误或包含额外字段 |
| 500 | `INTERNAL_ERROR` | 未预期异常 |

## 6. 供应商配置

LLM 与 Embedding 不再通过 `/split` 请求体传入，而是统一从 `.env` 或环境变量读取：

- `SPLITTER_LLM_PROVIDER`
- `SPLITTER_LLM_MODEL`
- `SPLITTER_LLM_BASE_URL`
- `SPLITTER_LLM_API_KEY`
- `SPLITTER_EMBEDDING_PROVIDER`
- `SPLITTER_EMBEDDING_MODEL`
- `SPLITTER_EMBEDDING_BASE_URL`
- `SPLITTER_EMBEDDING_API_KEY`

`/split` 响应不会回显 provider 配置、诊断信息或 API Key 明文。

## 7. LlamaIndex/LangChain 适配

所有策略均直接使用 LlamaIndex、LangChain 或 Chonkie 已实现的 parser/splitter。本项目只负责请求模型、provider 配置、parser 构造和 `StandardNode` 响应标准化。

自然语言类策略使用更适合 API 验证的默认窗口：`SentenceSplitter`、`TokenTextSplitter` 默认 `chunk_size=128`，`LangchainNodeParser` 与 `Chunker` 默认使用约 240 字符的窗口。`SentenceWindowNodeParser` 会使用兼容中英文句末标点的 sentence splitter。
