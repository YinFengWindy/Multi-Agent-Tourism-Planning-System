# 分布式多 Agent 协同旅游规划系统

这是一个面向生产场景的旅游决策与行程编排系统设计稿，目标是在 `Python + FastAPI + LangGraph + MCP + Redis + MongoDB + Docker + Vue 3` 技术栈下，构建可扩展、可观测、可重规划的分布式多 Agent 协作平台。

## 1. 设计目标

- 支持跨城市、多天、多约束的复杂旅游规划
- 通过 Parent Agent + 领域子 Agent 协作提升规划质量
- 采用 `Plan-Execute-Replan` 与 `ReAct` 闭环提升动态修正能力
- 通过 MCP 工具网关统一接入地图、天气、交通、酒店等第三方服务
- 结合 Redis 缓存与 MongoDB 快照存储，降低重复查询开销并提升响应速度
- 提供面向 Web 的可视化交互、流式规划过程展示和结果回溯能力

## 2. 核心能力

### 2.1 Agent 协同

- `Parent Agent`：理解用户需求、拆解任务、调度子 Agent、整合方案、触发重规划
- `Transport Agent`：火车/航班/市内交通方案搜索与时间可达性评估
- `Hotel Agent`：住宿区域、价格、评分、交通便利性和入住策略推荐
- `Route Agent`：景点顺序、日程节奏、地理聚类和换乘路径优化
- `Attraction Agent`：POI 筛选、开放时间、门票、预约和候选点补全
- `Budget Agent`：费用拆分、预算预警、替代方案推荐与性价比评分
- `Risk Agent`：天气、拥堵、闭园、节假日人流等风险感知与预案生成

### 2.2 分布式执行

- `Planner Service` 承载 LangGraph 编排图和 Parent Agent 状态机
- `Agent Worker` 集群按领域能力横向扩展，消费 Redis Streams 任务
- `MCP Gateway` 提供标准化工具协议、鉴权、限流、熔断和结果归一化
- `API Gateway` 提供统一对外接口、JWT 鉴权、会话管理和 SSE 流式输出
- `Vue 3` 前端负责规划输入、协作过程可视化、方案对比和重规划交互

## 3. 推荐架构

推荐采用“中心编排 + 分布式领域执行 + 工具网关”的混合架构：

1. 前端提交旅行意图、预算、时间、偏好和约束
2. `API Gateway` 完成鉴权、参数校验、会话创建与请求转发
3. `Planner Service` 启动 LangGraph 工作流，生成初始计划
4. Parent Agent 并行派发多个领域子任务到 `Agent Worker`
5. 子 Agent 通过 `MCP Gateway` 调用地图、天气、交通、酒店等工具
6. Parent Agent 汇总结果，执行冲突检测、质量打分和必要重规划
7. 结果持久化至 MongoDB，并将热点结果与工具摘要写入 Redis
8. 前端实时接收推理过程、推荐结果和备选方案

详细架构见：

- `docs/architecture-options.md`
- `docs/architecture.md`
- `docs/api-design.md`
- `docs/deployment.md`
- `docs/roadmap.md`

## 4. 当前目录结构

```text
Multi-Agent Tourism Planning System/
├─ README.md
├─ .env.example
├─ .gitignore
├─ docker-compose.yml
├─ docs/
│  ├─ architecture-options.md
│  ├─ architecture.md
│  ├─ api-design.md
│  ├─ deployment.md
│  └─ roadmap.md
├─ backend/
│  ├─ Dockerfile
│  ├─ requirements.txt
│  ├─ app/
│  ├─ apps/
│  ├─ tests/
│  └─ README.md
└─ frontend/
   ├─ Dockerfile
   ├─ package.json
   ├─ src/
   └─ README.md
```

## 5. 关键设计决策

- 编排框架：使用 `LangGraph`，适合显式状态机、并行节点和重规划控制
- 分布式调度：使用 `Redis Streams` 作为轻量任务总线，降低额外基础设施复杂度
- 会话存储：Redis 存短期上下文、速率限制、工具缓存；MongoDB 存计划快照、审计和结果版本
- 工具层标准化：所有外部 API 统一经过 `MCP Gateway` 进行签名、限流、Schema 校验和兜底
- 安全基线：JWT、RBAC、请求签名、速率限制、PII 脱敏、工具白名单、审计日志

## 6. 交付内容说明

当前交付已升级为 **可运行 MVP 成品**，包含：

- `API Gateway`：对外 REST + SSE 代理
- `Planner Service`：基于 `LangGraph` 的 Parent Agent 状态机与自动重规划
- `Agent Workers`：交通、住宿、路线、景点、预算、风险六类 Agent 协同执行
- `MCP Gateway`：可缓存的工具协议统一入口
- `Vue 3` 前端：规划表单、协同进度、最终结果与预算收紧重规划
- Docker Compose 启动方式、依赖声明与基础测试

## 7. 本地运行

### 7.1 Docker 方式

```bash
cd "Multi-Agent Tourism Planning System"
docker compose up --build
```

启动后访问：

- 前端：`http://localhost:5173`
- API Gateway：`http://localhost:8000`
- Planner Service：`http://localhost:8001`
- MCP Gateway：`http://localhost:8002`
- Agent Workers：`http://localhost:8003`

### 7.2 本地开发方式

后端：

```bash
cd "Multi-Agent Tourism Planning System/backend"
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn apps.mcp_gateway.main:app --reload --port 8002
uvicorn apps.agent_workers.main:app --reload --port 8003
uvicorn apps.planner_service.main:app --reload --port 8001
uvicorn apps.api_gateway.main:app --reload --port 8000
```

前端：

```bash
cd "Multi-Agent Tourism Planning System/frontend"
npm install
npm run dev
```

## 8. 下一步增强建议

建议按以下顺序启动开发：

1. 先完成 `API Gateway`、`Planner Service` 和 `MCP Gateway` 的最小闭环
2. 落地 `Transport Agent`、`Hotel Agent`、`Route Agent` 三个核心子 Agent
3. 打通 Redis 缓存、MongoDB 快照与前端流式展示
4. 再补齐预算、风险和多方案对比能力
5. 最后进入监控、安全、压测与灰度发布阶段
