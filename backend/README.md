# 后端工程设计与运行说明

## 1. 建议职责拆分

### `apps/api-gateway`

- 负责对外 REST API、SSE、JWT、Rate limiting
- 对接前端并转发到 Planner Service

### `apps/planner-service`

- 承载 LangGraph Parent Agent
- 负责状态机、任务拆解、结果聚合、重规划

### `apps/agent-workers`

- 负责领域子 Agent 执行
- 消费 Redis Streams 或任务队列

### `apps/mcp-gateway`

- 统一封装第三方 API
- 提供工具 Schema、超时、缓存、熔断和结果归一化

### `libs/common`

- 配置、日志、异常、追踪、鉴权中间件

### `libs/schemas`

- Pydantic 模型
- 计划结构、任务协议、工具契约、事件模型

## 2. 当前目录草图

```text
backend/
├─ Dockerfile
├─ requirements.txt
├─ apps/
│  ├─ api-gateway/
│  ├─ planner-service/
│  ├─ agent-workers/
│  └─ mcp-gateway/
├─ app/
│  ├─ config.py
│  ├─ models.py
│  ├─ tool_runtime.py
│  ├─ agent_runtime.py
│  ├─ planning_engine.py
│  ├─ plan_store.py
│  ├─ cache.py
│  └─ security.py
└─ tests/
```

## 3. 推荐后端依赖

- `fastapi`
- `uvicorn`
- `langgraph`
- `pydantic`
- `redis`
- `motor` 或 `pymongo`
- `httpx`
- `pyjwt`
- `tenacity`
- `orjson`
- `sse-starlette`

## 4. 当前实现状态

- `apps/api_gateway/main.py`：暴露 `/api/v1/plans`、`/stream`、`/replan`
- `apps/planner_service/main.py`：后台异步启动 LangGraph 规划任务并输出 SSE
- `apps/agent_workers/main.py`：执行 6 类领域 Agent 任务
- `apps/mcp_gateway/main.py`：统一执行 `weather_forecast`、`transport_search`、`hotel_search`、`poi_search`、`route_matrix`
- `tests/test_planning_engine.py`：覆盖缓存命中与规划结果生成

## 5. 关键实现要点

- Parent Agent 的状态必须结构化，不要把全部对话拼成单一长文本
- 子 Agent 输出统一为结构化对象，便于聚合和验证
- 所有工具调用必须带 `trace_id`、`plan_id`、`task_id`
- 领域任务建议设置最大重试次数和超时预算

## 6. 运行命令

```bash
pip install -r requirements.txt
uvicorn apps.mcp_gateway.main:app --reload --port 8002
uvicorn apps.agent_workers.main:app --reload --port 8003
uvicorn apps.planner_service.main:app --reload --port 8001
uvicorn apps.api_gateway.main:app --reload --port 8000
```
