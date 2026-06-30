# Splitter Implementation Task Plan

| Task ID | Added At | Priority | Area | Task | Depends On | Status |
|---|---|---:|---|---|---|---|
| SPLIT-001 | 2026-06-30 12:49 +08:00 | P0 | Planning | Create implementation task plan and issue log files | - | Done |
| SPLIT-002 | 2026-06-30 12:49 +08:00 | P0 | Design | Expand README concept into detailed technical design documentation | SPLIT-001 | Done |
| SPLIT-003 | 2026-06-30 12:49 +08:00 | P0 | API | Produce OpenAPI 3.1.0 specification and API usage documentation | SPLIT-002 | Done |
| SPLIT-004 | 2026-06-30 12:49 +08:00 | P0 | Architecture | Scaffold layered FastAPI/uv project structure | SPLIT-002 | Done |
| SPLIT-005 | 2026-06-30 12:49 +08:00 | P0 | Domain | Implement Pydantic data models, errors, and strategy/provider protocols | SPLIT-004 | Done |
| SPLIT-006 | 2026-06-30 12:49 +08:00 | P0 | Services | Implement source loading for text, base64/plain files, and URLs | SPLIT-005 | Done |
| SPLIT-007 | 2026-06-30 12:49 +08:00 | P0 | Strategies | Implement strategy registry and splitter strategies for file/text/relation parser families | SPLIT-005 | Done |
| SPLIT-008 | 2026-06-30 12:49 +08:00 | P0 | API | Implement `/api/v1/split`, `/api/v1/strategies`, and `/healthz` routes | SPLIT-006, SPLIT-007 | Done |
| SPLIT-009 | 2026-06-30 12:49 +08:00 | P1 | Deployment | Add Linux Python deployment guide plus Dockerfile/docker-compose assets | SPLIT-008 | Done |
| SPLIT-010 | 2026-06-30 12:49 +08:00 | P1 | Quality | Add focused tests for routing, split strategies, and API behavior | SPLIT-008 | Done |
| SPLIT-011 | 2026-06-30 12:49 +08:00 | P1 | Verification | Run lock/test verification, record any issues in `splitter-logs.md`, and update statuses | SPLIT-010 | Done |
| SPLIT-012 | 2026-06-30 13:20 +08:00 | P0 | Refactor | Adapt imports, packaging, Docker, and docs to flattened `src/` layout | SPLIT-011 | Done |
| SPLIT-013 | 2026-06-30 13:20 +08:00 | P0 | Providers | Add `.env` based default LLM/Embedding configuration and wire it through ProviderFactory | SPLIT-012 | Done |
| SPLIT-014 | 2026-06-30 13:20 +08:00 | P1 | Strategies | Add initial optional LlamaIndex/LangChain framework adapters | SPLIT-012 | Done |
| SPLIT-015 | 2026-06-30 13:20 +08:00 | P1 | Verification | Re-lock dependencies and verify tests/runtime after flattened layout changes | SPLIT-012, SPLIT-013, SPLIT-014 | Done |
| SPLIT-016 | 2026-06-30 13:45 +08:00 | P0 | Strategies | Replace hand-written splitter fallbacks with thin LlamaIndex/LangChain/Chonkie adapters for all 12 strategies | SPLIT-015 | Done |
| SPLIT-017 | 2026-06-30 15:05 +08:00 | P0 | API | Simplify `/api/v1/split` request to `content` and `mode`, removing file and URL input support | SPLIT-016 | Done |
| SPLIT-018 | 2026-06-30 15:30 +08:00 | P0 | API | Remove `diagnostics` from split responses and add 12 strategy request examples to runtime Swagger | SPLIT-017 | Done |
| SPLIT-019 | 2026-06-30 15:50 +08:00 | P0 | Dependencies | Add the tree-sitter language pack required by LlamaIndex `CodeSplitter` and cover the Swagger sample with a regression test | SPLIT-018 | Done |
| SPLIT-020 | 2026-06-30 16:55 +08:00 | P0 | Strategies | Tune natural-language splitter defaults, add Chinese sentence splitting, enable default Chunker dependency, and verify all Swagger strategy samples | SPLIT-019 | Done |
