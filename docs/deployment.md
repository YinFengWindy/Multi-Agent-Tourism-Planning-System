# 部署与运维设计

## 1. 环境划分

建议至少划分三套环境：

- `dev`：本地联调与单机 Docker Compose
- `staging`：联调、压测、回归测试
- `prod`：多实例部署、独立监控与告警

## 2. Docker 化部署建议

### 2.1 服务拆分

- `frontend`
- `api-gateway`
- `planner-service`
- `agent-workers`
- `mcp-gateway`
- `redis`
- `mongodb`

### 2.2 容器边界建议

- `api-gateway` 与 `planner-service` 分开部署，避免长链规划阻塞 API 接入层
- `agent-workers` 采用同镜像多副本模式，通过环境变量指定能力类型或复合能力集
- `mcp-gateway` 单独部署，便于统一维护密钥、限流和工具路由策略

## 3. 扩容策略

### 3.1 横向扩容对象

- `api-gateway`：按 QPS 扩容
- `planner-service`：按并发会话数扩容
- `agent-workers`：按任务堆积量与热点领域扩容
- `mcp-gateway`：按工具调用吞吐扩容

### 3.2 推荐指标

- Redis Streams backlog
- 每类 Agent 平均耗时
- 规划完成率
- 重规划触发率
- MCP 工具成功率与超时率
- LLM Token 消耗和缓存命中率

## 4. 可观测性

推荐引入以下可观测能力：

- OpenTelemetry Trace：跟踪一次规划经过哪些 Agent 和工具
- Metrics：请求耗时、错误率、缓存命中率、工具成功率
- Logging：结构化日志，统一 trace_id、plan_id、task_id
- Dashboard：按城市、节假日、用户类型看系统压力与结果质量

## 5. 安全设计

### 5.1 接口安全

- JWT 鉴权
- Refresh Token
- Rate limiting
- CORS 白名单
- 请求签名与时间戳校验

### 5.2 工具安全

- 工具白名单
- 参数 Schema 校验
- 敏感响应字段过滤
- 第三方 API 密钥集中管理
- 工具级限流与熔断

### 5.3 数据安全

- MongoDB 敏感字段加密
- Redis 禁止存储长期敏感原文
- 导出分享链接设置过期时间
- 审计日志不可篡改或异步归档

## 6. 故障处理与降级

### 6.1 外部工具异常

- 超时后回退最近成功缓存
- 若缓存不可用，返回“可参考但需二次确认”的备选方案
- 关键工具连续失败时触发熔断和告警

### 6.2 Agent 执行异常

- 单个子 Agent 失败不直接中断整体流程
- Parent Agent 将该领域标记为低置信度并尝试降级重试
- 达到阈值后返回人工确认建议或展示风险标记

### 6.3 数据存储异常

- Redis 异常时关闭缓存能力但保留核心规划
- MongoDB 异常时降级为短期内存快照，同时限制可回放历史功能

## 7. 生产环境推荐拓扑

- 前端通过 Nginx 或 CDN 分发静态资源
- API Gateway 和 Planner Service 部署为多实例无状态服务
- Agent Worker 根据能力标签独立部署多个 Deployment
- Redis 建议哨兵或托管版
- MongoDB 建议副本集
- MCP Gateway 单独做灰度发布，避免工具层变更影响整体业务

## 8. CI/CD 建议

- `PR` 阶段执行 lint、单测、契约测试
- `staging` 自动部署并做回归和冒烟测试
- `prod` 采用蓝绿或金丝雀发布
- 关键变更前后比对指标：规划成功率、平均时延、工具成功率、缓存命中率
