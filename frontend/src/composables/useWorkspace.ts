import { computed, ref, watch } from 'vue'

import { buildPlanStreamUrl, createPlan, fetchPlan, fetchRecentPlans, fetchSystemHealth, replanPlan } from '../api'
import { applyTheme, getStoredTheme, normalizeThemeColor, themePresets, type ThemeMode } from '../theme'
import type {
  PlanEnvelope,
  PlanEvent,
  PlanRequest,
  PlanResult as PlanResultModel,
  PlanSummary,
  SystemHealthResponse,
} from '../types'

const STORAGE_KEYS = {
  lastPlanId: 'mtp-last-plan-id',
  lastPayload: 'mtp-last-plan-payload',
}

const loading = ref(false)
const error = ref('')
const events = ref<PlanEvent[]>([])
const result = ref<PlanResultModel | undefined>()
const currentPlanId = ref('')
const lastPayload = ref<PlanRequest | null>(null)
const recentPlans = ref<PlanSummary[]>([])
const serviceHealth = ref<SystemHealthResponse | null>(null)
const healthLoading = ref(false)
const themeMode = ref<ThemeMode>('light')
const accentColor = ref(themePresets[0].accent)

const workflowCapsules = [
  'Parent Agent',
  '6 个领域 Agent',
  'Plan-Execute-Replan',
  'ReAct 推理闭环',
  'MCP 工具网关',
  'Redis / MongoDB',
]

let eventSource: EventSource | null = null
let initialized = false
let themeWatchInitialized = false

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
const healthSummary = computed(() => {
  const services = serviceHealth.value?.services ?? []
  const healthyCount = services.filter((service) => service.status === 'ok').length
  return {
    overall: serviceHealth.value?.status ?? 'unknown',
    healthyCount,
    total: services.length,
  }
})
const completionRate = computed(() => {
  const done = workspaceStages.value.filter((stage) => stage.done).length
  return Math.round((done / workspaceStages.value.length) * 100)
})

function persistWorkspaceSession() {
  if (typeof window === 'undefined') {
    return
  }
  if (currentPlanId.value) {
    window.localStorage.setItem(STORAGE_KEYS.lastPlanId, currentPlanId.value)
  }
  if (lastPayload.value) {
    window.localStorage.setItem(STORAGE_KEYS.lastPayload, JSON.stringify(lastPayload.value))
  }
}

function restoreWorkspaceSession() {
  if (typeof window === 'undefined') {
    return { planId: '', payload: null as PlanRequest | null }
  }

  const storedPlanId = window.localStorage.getItem(STORAGE_KEYS.lastPlanId) ?? ''
  const storedPayload = window.localStorage.getItem(STORAGE_KEYS.lastPayload)

  let parsedPayload: PlanRequest | null = null
  if (storedPayload) {
    try {
      parsedPayload = JSON.parse(storedPayload) as PlanRequest
    } catch {
      parsedPayload = null
    }
  }

  return { planId: storedPlanId, payload: parsedPayload }
}

function resetStream() {
  events.value = []
  result.value = undefined
  error.value = ''
  if (eventSource) {
    eventSource.close()
    eventSource = null
  }
}

async function refreshRecentPlans(limit = 8) {
  try {
    const response = await fetchRecentPlans(limit)
    recentPlans.value = response.items
  } catch {
    recentPlans.value = recentPlans.value
  }
}

async function refreshServiceHealth() {
  healthLoading.value = true
  try {
    serviceHealth.value = await fetchSystemHealth()
  } finally {
    healthLoading.value = false
  }
}

async function refreshResult(planId: string) {
  try {
    const envelope = await fetchPlan(planId)
    loading.value = false
    currentPlanId.value = planId
    lastPayload.value = envelope.request
    events.value = envelope.events
    persistWorkspaceSession()
    if (eventSource) {
      eventSource.close()
      eventSource = null
    }
    if (envelope.status === 'failed') {
      error.value = envelope.error ?? '规划失败'
      await refreshRecentPlans()
      return
    }
    result.value = (envelope as PlanEnvelope).result
    await refreshRecentPlans()
  } catch (reason) {
    loading.value = false
    error.value = reason instanceof Error ? reason.message : '获取结果失败'
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

async function handleResumePlan(planId: string) {
  resetStream()
  currentPlanId.value = planId
  loading.value = true
  persistWorkspaceSession()
  try {
    const envelope = await fetchPlan(planId)
    events.value = envelope.events
    lastPayload.value = envelope.request
    currentPlanId.value = envelope.plan_id
    persistWorkspaceSession()

    if (envelope.status === 'planning') {
      openStream(planId)
      return
    }

    loading.value = false
    if (envelope.status === 'failed') {
      error.value = envelope.error ?? '规划失败'
      result.value = undefined
      await refreshRecentPlans()
      return
    }
    result.value = envelope.result
    await refreshRecentPlans()
  } catch (reason) {
    loading.value = false
    error.value = reason instanceof Error ? reason.message : '恢复规划失败'
  }
}

async function handleCreatePlan(payload: PlanRequest) {
  resetStream()
  loading.value = true
  lastPayload.value = payload
  try {
    const response = await createPlan(payload)
    currentPlanId.value = response.plan_id
    persistWorkspaceSession()
    await refreshRecentPlans()
    openStream(response.plan_id)
  } catch (reason) {
    loading.value = false
    error.value = reason instanceof Error ? reason.message : '创建规划失败'
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
  persistWorkspaceSession()
  try {
    await replanPlan(currentPlanId.value, { budget: tightenedBudget, hotel_level: '经济型' })
    await refreshRecentPlans()
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
  themeMode.value = 'light'
  accentColor.value = themePresets[0].accent
}

function initializeWorkspace() {
  if (!initialized) {
    const stored = getStoredTheme()
    const session = restoreWorkspaceSession()
    themeMode.value = stored.mode
    accentColor.value = stored.accent
    currentPlanId.value = session.planId
    lastPayload.value = session.payload
    initialized = true

    void refreshRecentPlans()
    void refreshServiceHealth()

    if (session.planId) {
      void handleResumePlan(session.planId)
    }
  }

  if (!themeWatchInitialized) {
    watch([themeMode, accentColor], ([mode, accent]) => {
      applyTheme(mode, accent)
    }, { immediate: true })
    themeWatchInitialized = true
  }
}

export function useWorkspace() {
  return {
    loading,
    error,
    events,
    result,
    currentPlanId,
    lastPayload,
    recentPlans,
    serviceHealth,
    healthLoading,
    themeMode,
    accentColor,
    workflowCapsules,
    workspaceStages,
    currentStatus,
    resultBudgetTotal,
    overviewMetrics,
    planHighlights,
    themeSummary,
    healthSummary,
    completionRate,
    handleCreatePlan,
    handleReplan,
    handleResumePlan,
    refreshRecentPlans,
    refreshServiceHealth,
    updateThemeMode,
    updateAccentColor,
    resetTheme,
    initializeWorkspace,
  }
}
