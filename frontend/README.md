# 前端工程设计与运行说明

## 1. 推荐职责

前端基于 `Vue 3`，主要负责：

- 旅行偏好与约束输入
- 流式查看规划过程
- 最终行程结果展示
- 多版本对比与重规划交互
- 分享、收藏、导出

## 2. 当前页面结构

```text
frontend/
├─ Dockerfile
├─ package.json
├─ src/
│  ├─ composables/
│  │  └─ useWorkspace.ts
│  ├─ components/
│  │  ├─ PlanForm.vue
│  │  ├─ PlanningStream.vue
│  │  ├─ PlanResult.vue
│  │  └─ ThemeCustomizer.vue
│  ├─ layouts/
│  │  └─ WorkspaceLayout.vue
│  ├─ views/
│  │  ├─ OverviewView.vue
│  │  ├─ ExecutionView.vue
│  │  ├─ ResultsView.vue
│  │  └─ ThemeView.vue
│  ├─ App.vue
│  ├─ api.ts
│  ├─ router.ts
│  ├─ theme.ts
│  ├─ types.ts
│  ├─ vite-env.d.ts
│  └─ main.ts
```

## 3. 核心交互建议

- 输入页支持城市、日期、人数、预算、偏好、出行方式、酒店档位、日程节奏等约束
- 规划过程页实时显示 Parent Agent 当前阶段、各子 Agent 进度和重规划原因
- 结果页展示日程卡片、路线图、住宿建议、预算拆分和风险提示
- 对比页展示不同版本之间的预算、耗时、景点覆盖率和舒适度差异

## 4. 状态管理建议

- 会话级：用户登录状态、偏好模板
- 规划级：当前计划、流式事件、当前版本、备选方案
- 展示级：筛选条件、排序方式、展开折叠状态

## 5. 当前实现能力

- 使用 SSE 接收规划进度
- 支持日间 / 夜间模式切换
- 支持预设主题与自定义主色
- 使用共享工作台外壳 + 独立路由页展示总览 / 执行 / 结果 / 主题
- 左侧导航支持 SaaS 控制台式多页面跳转
- 使用卡片式结果页可视化每日行程路径与建议
- 结果页包含地图占位、路线分析、预算矩阵与 Agent 洞察
- 支持移动端响应式布局
- 对风险项使用显著颜色和标签提示
- 已统一品牌图标：使用“轨道 + 目的地图钉 + 星芒”图形，同时应用到站内品牌位与浏览器 favicon
- 新增系统健康面板：总览页可查看 API Gateway / Planner / Agent Workers / MCP Gateway 的当前状态
- 新增最近规划列表：支持从总览页恢复最近会话，减少刷新后重复操作
- 约束表单支持快速模板与提交前校验，适合直接演示或继续扩展成生产输入体验
- 结果页已升级为更强的分析视图：支持路线强度、天气稳定性、Agent 置信度和工具摘要展示
- 结果页支持复制简版行程摘要，便于发到 IM、评审文档或工单系统
- 总览页现已切换为聊天主入口，用户可直接以自然语言提出旅游需求
- 支持用户填写自己的 `OpenAI-compatible` 模型配置（`API Base URL / API Key / Model`），并通过对话触发创建或修改规划
- 前端整体视觉已切换为浅色门户式风格：左侧极简导航、居中英雄区、大输入卡与发现流卡片
- 首页现通过后端 `portal home` 接口获取功能卡片与发现流内容，用于承载平台化首页样式
- 执行页、结果页、主题页已统一切换为门户化浅色风格，页面头部、指标卡和辅助面板与首页视觉保持一致

## 6. 运行命令

```bash
npm install
npm run dev
```
