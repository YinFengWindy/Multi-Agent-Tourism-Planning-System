<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'

import { buildPlanStreamUrl, createPlan, fetchPlan, replanPlan } from './api'
import PlanForm from './components/PlanForm.vue'
import PlanResultPanel from './components/PlanResult.vue'
import PlanningStream from './components/PlanningStream.vue'
import ThemeCustomizer from './components/ThemeCustomizer.vue'
import { applyTheme, getStoredTheme, normalizeThemeColor, themePresets, type ThemeMode } from './theme'
import type { PlanEnvelope, PlanEvent, PlanRequest, PlanResult as PlanResultModel } from './types'

const loading = ref(false)
const error = ref('')
const events = ref<PlanEvent[]>([])
const result = ref<PlanResultModel | undefined>()
const currentPlanId = ref('')
const lastPayload = ref<PlanRequest | null>(null)
const themeMode = ref<ThemeMode>('dark')
const accentColor = ref('#4f8cff')
let eventSource: EventSource | null = null

const workflowCapsules = [
  'Parent Agent',
  '6 个领域 Agent',
  'Plan-Execute-Replan',
  'ReAct 推理闭环',
  'MCP 工具网关',
  'Redis / MongoDB',
]

const workspaceStages = computed(() => {
  const eventTypes = new Set(events.value.map((event) => event.type))
  return [
    { label: '需求解析', active: eventTypes.has('plan_started'), done: eventTypes.has('plan_started') },
    { label: '任务分发', active: eventTypes.has('task_dispatched'), done: eventTypes.has('task_dispatched') },
    { label: '领域执行', active: eventTypes.has('agent_progress'), done: eventTypes.has('agent_progress') },
    { label: '自动重规划', active: eventTypes.has('replan_triggered'), done: eventTypes.has('replan_triggered') },
    { label: '最终成品', active: eventTypes.has('plan_completed'), done: eventTypes.has('plan_completed') },
  ]
})

const currentStatus = computed(() => {
  if (loading.value) {
    return '规划运行中'
  }
  if (result.value) {
    return '规划已完成'
  }
  return '等待输入'
})

const resultBudgetTotal = computed(() => {
  if (!result.value) {
    return 0
  }
  return Object.values(result.value.budget_breakdown ?? {}).reduce((sum, value) => sum + Number(value || 0), 0)
})

const overviewMetrics = computed(() => [
  { label: '当前状态', value: currentStatus.value, hint: '实时反映规划生命周期' },
  { label: '事件流', value: `${events.value.length} 条`, hint: '展示 Parent 与子 Agent 进度' },
  { label: '行程天数', value: result.value ? `${result.value.days.length} 天` : '--', hint: '自动输出时间轴成品' },
  { label: '预算总览', value: resultBudgetTotal.value ? `¥${Math.round(resultBudgetTotal.value)}` : '--', hint: '汇总交通住宿门票餐饮' },
])

const planHighlights = computed(() => {
  if (!result.value) {
    return [
      '支持日间 / 夜间模式',
      '支持自定义主题主色',
      '展示多 Agent 协同过程',
    ]
  }
  return [
    result.value.summary,
    result.value.warnings.length ? `风险提醒 ${result.value.warnings.length} 条` : '暂无高优先级风险',
    result.value.fallback_plans.length ? `可用备选预案 ${result.value.fallback_plans.length} 条` : '无备选预案',
  ]
})

const themeSummary = computed(() => `${themeMode.value === 'dark' ? '夜间模式' : '日间模式'} · ${accentColor.value.toUpperCase()}`)

function resetStream() {
  events.value = []
  result.value = undefined
  error.value = ''
  if (eventSource) {
    eventSource.close()
    eventSource = null
  }
}

async function handleCreatePlan(payload: PlanRequest) {
  resetStream()
  loading.value = true
  lastPayload.value = payload
  try {
    const response = await createPlan(payload)
    currentPlanId.value = response.plan_id
    openStream(response.plan_id)
  } catch (reason) {
    loading.value = false
    error.value = reason instanceof Error ? reason.message : '创建规划失败'
  }
}

function openStream(planId: string) {
  eventSource = new EventSource(buildPlanStreamUrl(planId))
  eventSource.onmessage = async (event) => {
    const parsed = JSON.parse(event.data) as PlanEvent
    events.value = [...events.value, parsed]
    if (parsed.type === 'plan_completed' || parsed.type === 'plan_failed') {
      await refreshResult(planId)
    }
  }
  eventSource.onerror = async () => {
    await refreshResult(planId)
  }
}

async function refreshResult(planId: string) {
  try {
    const envelope = await fetchPlan(planId)
    loading.value = false
    if (eventSource) {
      eventSource.close()
      eventSource = null
    }
    if (envelope.status === 'failed') {
      error.value = envelope.error ?? '规划失败'
      return
    }
    result.value = (envelope as PlanEnvelope).result
  } catch (reason) {
    loading.value = false
    error.value = reason instanceof Error ? reason.message : '获取结果失败'
  }
}

async function handleReplan() {
  if (!currentPlanId.value || !lastPayload.value) {
    return
  }
  resetStream()
  loading.value = true
  const tightenedBudget = Math.max(800, Math.round(lastPayload.value.budget * 0.9))
  lastPayload.value = { ...lastPayload.value, budget: tightenedBudget }
  try {
    await replanPlan(currentPlanId.value, { budget: tightenedBudget, hotel_level: '经济型' })
    openStream(currentPlanId.value)
  } catch (reason) {
    loading.value = false
    error.value = reason instanceof Error ? reason.message : '重规划失败'
  }
}

function updateThemeMode(mode: ThemeMode) {
  themeMode.value = mode
}

function updateAccentColor(color: string) {
  accentColor.value = normalizeThemeColor(color)
}

function resetTheme() {
  themeMode.value = 'dark'
  accentColor.value = themePresets[0].accent
}

watch([themeMode, accentColor], ([mode, accent]) => {
  applyTheme(mode, accent)
})

onMounted(() => {
  const stored = getStoredTheme()
  themeMode.value = stored.mode
  accentColor.value = stored.accent
  applyTheme(stored.mode, stored.accent)
})
</script>

<template>
  <main class="page-shell">
    <section class="workspace-toolbar glass-panel">
      <div class="toolbar-brand">
        <div class="brand-mark">M</div>
        <div>
          <strong>AI Tourism Workspace</strong>
          <small>Professional Multi-Agent Planning Console</small>
        </div>
      </div>

      <div class="toolbar-meta">
        <span class="toolbar-chip">{{ themeSummary }}</span>
        <span class="toolbar-chip">{{ currentStatus }}</span>
        <span class="toolbar-chip">目标目录：Multi-Agent Tourism Planning System</span>
      </div>
    </section>

    <section class="hero-shell glass-panel">
      <div class="hero-copy">
        <span class="eyebrow">Professional Planning Workspace</span>
        <h1>Multi-Agent Tourism Planning System</h1>
        <p class="hero-description">
          面向生产级旅游规划场景的专业版 AI 工作台，支持日间 / 夜间模式、自定义品牌色、
          多 Agent 协同执行可视化，以及可回放的规划与重规划过程。
        </p>

        <div class="capsule-row">
          <span v-for="item in workflowCapsules" :key="item" class="capsule">{{ item }}</span>
        </div>

        <div class="metric-grid">
          <article v-for="metric in overviewMetrics" :key="metric.label" class="metric-card surface-card">
            <span class="metric-label">{{ metric.label }}</span>
            <strong class="metric-value">{{ metric.value }}</strong>
            <small class="metric-hint">{{ metric.hint }}</small>
          </article>
        </div>

        <div class="stage-rail surface-card">
          <article
            v-for="stage in workspaceStages"
            :key="stage.label"
            :class="['stage-chip', { active: stage.active, done: stage.done }]"
          >
            <span class="stage-dot"></span>
            <span>{{ stage.label }}</span>
          </article>
        </div>
      </div>

      <div class="hero-side">
        <ThemeCustomizer
          :mode="themeMode"
          :accent="accentColor"
          :presets="themePresets"
          @update:mode="updateThemeMode"
          @update:accent="updateAccentColor"
          @reset="resetTheme"
        />
      </div>
    </section>

    <section class="workspace-grid">
      <div class="left-rail">
        <PlanForm @submit="handleCreatePlan" />
        <PlanningStream :events="events" :loading="loading" />
      </div>

      <div class="right-rail">
        <section class="summary-panel glass-panel">
          <div class="summary-header">
            <div>
              <span class="eyebrow">Workspace Summary</span>
              <h2>执行概览</h2>
            </div>
            <span :class="['status-pill', loading ? 'running' : result ? 'completed' : 'idle']">
              {{ currentStatus }}
            </span>
          </div>
          <ul class="summary-list">
            <li v-for="item in planHighlights" :key="item">
              <span class="summary-dot"></span>
              <span>{{ item }}</span>
            </li>
          </ul>
          <div v-if="error" class="error-banner">{{ error }}</div>
        </section>

        <PlanResultPanel :result="result" @replan="handleReplan" />
      </div>
    </section>
  </main>
</template>

<style scoped>
.page-shell {
  max-width: 1440px;
  margin: 0 auto;
  padding: 28px 20px 56px;
}

.workspace-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin-bottom: 18px;
  padding-block: 18px;
}

.toolbar-brand {
  display: flex;
  align-items: center;
  gap: 14px;
}

.brand-mark {
  width: 44px;
  height: 44px;
  border-radius: 16px;
  display: grid;
  place-items: center;
  background: linear-gradient(135deg, var(--accent), var(--accent-strong));
  color: var(--accent-contrast);
  font-size: 20px;
  font-weight: 800;
  box-shadow: 0 12px 26px rgba(var(--accent-rgb), 0.24);
}

.toolbar-brand strong {
  display: block;
  font-size: 15px;
}

.toolbar-brand small {
  color: var(--text-muted);
}

.toolbar-meta {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 10px;
}

.toolbar-chip {
  display: inline-flex;
  align-items: center;
  padding: 10px 14px;
  border-radius: 999px;
  border: 1px solid var(--border-color);
  background: rgba(var(--accent-rgb), 0.08);
  color: var(--text-secondary);
  font-size: 13px;
}

.hero-shell {
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(320px, 420px);
  gap: 22px;
  margin-bottom: 22px;
}

.hero-copy {
  display: grid;
  gap: 20px;
}

.hero-description {
  max-width: 820px;
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.8;
  font-size: 16px;
}

.eyebrow {
  display: inline-flex;
  color: var(--accent);
  text-transform: uppercase;
  letter-spacing: 0.14em;
  font-size: 12px;
}

.hero-copy h1 {
  margin: 0;
  font-size: clamp(34px, 5vw, 54px);
  line-height: 1.05;
}

.capsule-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.capsule {
  display: inline-flex;
  align-items: center;
  padding: 10px 14px;
  border-radius: 999px;
  background: rgba(var(--accent-rgb), 0.1);
  color: var(--accent-strong);
  border: 1px solid rgba(var(--accent-rgb), 0.18);
  font-size: 13px;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
}

.metric-card {
  display: grid;
  gap: 8px;
}

.metric-label {
  color: var(--text-muted);
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.metric-value {
  font-size: 22px;
}

.metric-hint {
  color: var(--text-muted);
  line-height: 1.5;
}

.stage-rail {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 10px;
}

.stage-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 46px;
  border-radius: 16px;
  border: 1px solid var(--border-color);
  background: var(--surface-strong);
  color: var(--text-muted);
  font-size: 13px;
}

.stage-chip.active {
  color: var(--accent-strong);
  background: rgba(var(--accent-rgb), 0.12);
  border-color: rgba(var(--accent-rgb), 0.25);
}

.stage-chip.done {
  box-shadow: inset 0 0 0 1px rgba(var(--accent-rgb), 0.08);
}

.stage-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: currentColor;
}

.hero-side {
  min-width: 0;
}

.workspace-grid {
  display: grid;
  grid-template-columns: minmax(0, 0.92fr) minmax(0, 1.08fr);
  gap: 20px;
}

.left-rail,
.right-rail {
  display: grid;
  gap: 18px;
}

.summary-panel {
  display: grid;
  gap: 16px;
}

.summary-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: center;
}

.summary-header h2 {
  margin: 6px 0 0;
  font-size: 28px;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  padding: 10px 14px;
  border-radius: 999px;
  font-size: 13px;
  border: 1px solid var(--border-color);
}

.status-pill.idle {
  background: var(--surface-muted);
  color: var(--text-secondary);
}

.status-pill.running {
  background: rgba(var(--accent-rgb), 0.14);
  color: var(--accent-strong);
  border-color: rgba(var(--accent-rgb), 0.26);
}

.status-pill.completed {
  background: rgba(var(--success-rgb), 0.14);
  color: var(--success);
  border-color: rgba(var(--success-rgb), 0.25);
}

.summary-list {
  display: grid;
  gap: 12px;
  list-style: none;
  padding: 0;
  margin: 0;
}

.summary-list li {
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--text-secondary);
}

.summary-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: var(--accent);
  box-shadow: 0 0 0 6px rgba(var(--accent-rgb), 0.12);
}

.error-banner {
  padding: 14px 16px;
  border-radius: 16px;
  background: rgba(var(--danger-rgb), 0.12);
  border: 1px solid rgba(var(--danger-rgb), 0.22);
  color: var(--danger);
}

@media (max-width: 1200px) {
  .metric-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .stage-rail {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 1024px) {
  .workspace-toolbar,
  .hero-shell,
  .workspace-grid {
    grid-template-columns: 1fr;
  }

  .workspace-toolbar {
    flex-direction: column;
    align-items: flex-start;
  }

  .toolbar-meta {
    justify-content: flex-start;
  }
}

@media (max-width: 640px) {
  .page-shell {
    padding-inline: 14px;
  }

  .metric-grid {
    grid-template-columns: 1fr;
  }

  .stage-rail {
    grid-template-columns: 1fr;
  }

  .summary-header {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
