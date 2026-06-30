# 部署架构与运行手册

## 1. 推荐拓扑

```mermaid
flowchart LR
    Client["Client / Internal Service"] --> LB["Nginx / API Gateway / Load Balancer"]
    LB --> App1["splitter-api:8000"]
    LB --> App2["splitter-api:8000"]
    App1 --> MaaS["LLM / Embedding Provider"]
    App2 --> MaaS
```

最小部署只需要一个 Linux 主机和一个 API 进程；生产环境建议通过 Nginx、Caddy、Traefik 或云厂商 API Gateway 负责 TLS、认证、限流和请求体大小限制。

## 2. 环境要求

- Linux x86_64/arm64
- Python 3.11+
- uv 0.5+ 或 Docker 24+
- 如启用需要远程模型的策略，服务器需要能访问对应 LLM/Embedding Provider

## 3. Python/uv 直接部署

```bash
git clone <repo-url> splitter
cd splitter
uv sync --no-dev
uv run uvicorn app:app --app-dir src --host 0.0.0.0 --port 8000
```

健康检查：

```bash
curl http://127.0.0.1:8000/healthz
```

示例请求：

```bash
curl -X POST http://127.0.0.1:8000/api/v1/split \
  -H 'Content-Type: application/json' \
  -d '{
    "content": "# Title\n\nHello splitter.",
    "mode": "auto"
  }'
```

## 4. systemd 服务

`/etc/systemd/system/splitter.service` 示例：

```ini
[Unit]
Description=Splitter API
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=/opt/splitter
Environment=PYTHONUNBUFFERED=1
ExecStart=/usr/local/bin/uv run uvicorn app:app --app-dir src --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3
User=splitter
Group=splitter

[Install]
WantedBy=multi-user.target
```

启用：

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now splitter
sudo systemctl status splitter
```

## 5. Docker 部署

构建：

```bash
docker build -t splitter-api:0.1.0 .
```

运行：

```bash
docker run --rm -p 8000:8000 splitter-api:0.1.0
```

## 6. Docker Compose 部署

```bash
docker compose up -d --build
docker compose logs -f splitter-api
```

## 7. 配置建议

| Env | Default | Description |
|---|---|---|
| `SPLITTER_APP_NAME` | `splitter` | 服务名 |
| `SPLITTER_APP_VERSION` | `0.1.0` | 版本 |
| `SPLITTER_LLM_PROVIDER` | - | 默认 LLM 供应商 |
| `SPLITTER_LLM_MODEL` | - | 默认 LLM 模型 |
| `SPLITTER_LLM_BASE_URL` | - | 默认 LLM API Base URL |
| `SPLITTER_LLM_API_KEY` | - | 默认 LLM API Key |
| `SPLITTER_EMBEDDING_PROVIDER` | - | 默认 Embedding 供应商 |
| `SPLITTER_EMBEDDING_MODEL` | - | 默认 Embedding 模型 |
| `SPLITTER_EMBEDDING_BASE_URL` | - | 默认 Embedding API Base URL |
| `SPLITTER_EMBEDDING_API_KEY` | - | 默认 Embedding API Key |

## 8. 生产注意事项

- 在反向代理层设置请求体大小限制，例如 Nginx `client_max_body_size 20m;`。
- 生产环境不要在请求中明文传长期 API Key；本服务默认从环境变量或密钥管理系统读取模型凭据。
- 开启访问日志、结构化应用日志和指标采集。
- `/split` 不再下载 URL；如未来重新引入远程内容加载，应在独立服务或隔离网络中处理 SSRF、防重定向和大小限制。
