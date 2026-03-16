# API 与数据模型设计

## 1. 对外 API

### 1.1 创建规划会话

`POST /api/v1/plans`

请求体示例：

```json
{
  "origin_city": "上海",
  "destination_cities": ["杭州", "乌镇"],
  "start_date": "2026-05-01",
  "end_date": "2026-05-04",
  "travelers": 2,
  "budget": 5000,
  "preferences": ["美食", "江南古镇", "轻松节奏"],
  "constraints": {
    "transport_mode": ["高铁"],
    "hotel_level": "舒适型",
    "daily_start_after": "09:00",
    "daily_end_before": "21:30"
  }
}
```

返回体示例：

```json
{
  "plan_id": "plan_01",
  "session_id": "sess_01",
  "status": "planning",
  "stream_url": "/api/v1/plans/plan_01/stream"
}
```

### 1.2 获取规划结果

`GET /api/v1/plans/{plan_id}`

返回字段建议：

- `summary`
- `days`
- `budget_breakdown`
- `transport_options`
- `hotel_options`
- `warnings`
- `fallback_plans`
- `version`

### 1.3 触发重规划

`POST /api/v1/plans/{plan_id}/replan`

适用场景：

- 用户修改预算
- 用户更换出发时间
- 某个景点不再想去
- 交通或天气发生变化

请求体示例：

```json
{
  "reason": "budget_exceeded",
  "updated_constraints": {
    "budget": 4200,
    "must_keep_poi": ["西湖", "灵隐寺"]
  }
}
```

### 1.4 流式进度

`GET /api/v1/plans/{plan_id}/stream`

SSE 事件类型建议：

- `plan_started`
- `task_dispatched`
- `agent_progress`
- `tool_called`
- `replan_triggered`
- `plan_completed`
- `plan_failed`

## 2. 内部服务 API

### 2.1 Planner Service → Agent Worker

`POST /internal/agent-tasks`

```json
{
  "task_id": "task_transport_01",
  "plan_id": "plan_01",
  "agent_type": "transport",
  "goal": "为上海到杭州乌镇四日行搜索高铁优先交通方案",
  "constraints": {
    "budget": 1200,
    "travelers": 2
  },
  "context_refs": ["ctx_01", "ctx_02"]
}
```

### 2.2 Agent Worker → MCP Gateway

`POST /internal/mcp/execute`

```json
{
  "tool_name": "route_search",
  "tool_version": "v1",
  "trace_id": "trace_01",
  "arguments": {
    "origin": "上海虹桥",
    "destination": "杭州东",
    "date": "2026-05-01"
  }
}
```

### 2.3 MCP Gateway 返回规范

```json
{
  "success": true,
  "source": "gaode",
  "latency_ms": 183,
  "cached": false,
  "data": {
    "items": []
  },
  "normalized_summary": "共返回 4 条高铁候选，最早 07:12 出发，最低票价 73 元"
}
```

## 3. 核心数据模型

### 3.1 Plan 文档

MongoDB 集合：`plans`

```json
{
  "plan_id": "plan_01",
  "user_id": "user_01",
  "status": "completed",
  "request": {},
  "summary": "杭州乌镇 4 天轻松游",
  "days": [
    {
      "date": "2026-05-01",
      "city": "杭州",
      "items": []
    }
  ],
  "budget_breakdown": {
    "transport": 800,
    "hotel": 1800,
    "tickets": 700,
    "food": 900,
    "local_transport": 300,
    "buffer": 500
  },
  "warnings": [],
  "version": 3,
  "created_at": "2026-03-16T22:00:00Z",
  "updated_at": "2026-03-16T22:10:00Z"
}
```

### 3.2 Plan Snapshot

MongoDB 集合：`plan_snapshots`

字段建议：

- `plan_id`
- `version`
- `state_graph_snapshot`
- `agent_outputs`
- `decision_summary`
- `replan_reason`
- `created_at`

### 3.3 Tool Cache

Redis Key 建议：

- `tool:route:{hash}`
- `tool:weather:{city}:{date}`
- `tool:hotel:{city}:{checkin}:{checkout}:{hash}`
- `semantic_cache:{embedding_hash}`

### 3.4 Agent Task Result

MongoDB 集合：`agent_task_results`

字段建议：

- `task_id`
- `plan_id`
- `agent_type`
- `status`
- `inputs`
- `outputs`
- `tool_calls`
- `confidence_score`
- `latency_ms`

## 4. MCP 工具契约建议

每个工具定义统一的输入输出 Schema：

- `name`
- `description`
- `input_schema`
- `output_schema`
- `timeout_seconds`
- `cache_ttl`
- `fallback_policy`

示例：

```json
{
  "name": "weather_forecast",
  "description": "查询某城市某日期天气预报",
  "input_schema": {
    "type": "object",
    "properties": {
      "city": { "type": "string" },
      "date": { "type": "string" }
    },
    "required": ["city", "date"]
  },
  "timeout_seconds": 5,
  "cache_ttl": 3600,
  "fallback_policy": "return_last_success_result"
}
```

## 5. 错误码建议

| 错误码 | 含义 |
| --- | --- |
| `PLAN_INVALID_INPUT` | 用户输入不合法 |
| `PLAN_CONTEXT_MISSING` | 关键约束缺失 |
| `TOOL_TIMEOUT` | 外部工具超时 |
| `TOOL_SCHEMA_ERROR` | 工具返回格式不匹配 |
| `REPLAN_REQUIRED` | 当前方案必须重规划 |
| `RATE_LIMITED` | 请求频率超限 |
| `AUTH_INVALID_TOKEN` | 鉴权失败 |

## 6. 前端页面模型

建议页面：

- `/planner/new`：新建规划
- `/planner/:id`：查看行程结果
- `/planner/:id/compare`：对比多个版本
- `/planner/:id/history`：查看重规划历史
- `/account/settings`：偏好、风格、预算模板
