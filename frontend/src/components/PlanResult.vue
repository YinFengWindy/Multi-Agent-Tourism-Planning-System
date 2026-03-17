<script setup lang="ts">
import { computed, ref } from 'vue'

import type { PlanResult as PlanResultModel } from '../types'

const props = defineProps<{
  result?: PlanResultModel
}>()

const emit = defineEmits<{
  replan: []
}>()

const budgetItems = computed(() => Object.entries(props.result?.budget_breakdown ?? {}))
const budgetTotal = computed(() => budgetItems.value.reduce((sum, [, value]) => sum + Number(value || 0), 0))
const insightEntries = computed(() => Object.entries(props.result?.domain_insights ?? {}))
const copyStatus = ref('复制摘要')
const budgetBars = computed(() =>
  budgetItems.value.map(([key, value]) => ({
    key,
    value: Number(value),
    percent: budgetTotal.value ? Math.max(8, (Number(value) / budgetTotal.value) * 100) : 0,
  })),
)

const cityAnchors: Record<string, { x: number; y: number }> = {
  上海: { x: 68, y: 74 },
  杭州: { x: 58, y: 62 },
  乌镇: { x: 52, y: 58 },
  苏州: { x: 48, y: 54 },
  北京: { x: 40, y: 20 },
  广州: { x: 36, y: 84 },
  深圳: { x: 40, y: 88 },
}

const mapStops = computed(() => {
  const days = props.result?.days ?? []
  const fallbackPositions = [
    { x: 24, y: 64 },
    { x: 40, y: 52 },
    { x: 58, y: 38 },
    { x: 74, y: 46 },
    { x: 82, y: 68 },
  ]

  return days.map((day, index) => ({
    label: `D${day.day_index}`,
    city: day.city,
    theme: day.theme,
    x: cityAnchors[day.city]?.x ?? fallbackPositions[index % fallbackPositions.length].x,
    y: cityAnchors[day.city]?.y ?? fallbackPositions[index % fallbackPositions.length].y,
  }))
})

const mapPolyline = computed(() => mapStops.value.map((stop) => `${stop.x},${stop.y}`).join(' '))
const routeSummary = computed(() =>
  (props.result?.days ?? []).map((day) => `Day ${day.day_index} · ${day.city} · ${day.theme}`),
)

const routeStats = computed(() => {
  const days = props.result?.days ?? []
  const cityCount = new Set(days.map((day) => day.city)).size
  const activityCount = days.reduce((sum, day) => sum + day.items.length, 0)
  const avgActivities = days.length ? (activityCount / days.length).toFixed(1) : '0.0'
  const budgetInsight = props.result?.domain_insights?.budget?.structured_data ?? {}
  const withinBudget = Boolean((budgetInsight as Record<string, unknown>).within_budget ?? false)

  return [
    { label: '覆盖城市', value: `${cityCount} 个`, hint: '本次路线跨越的城市数' },
    { label: '活动密度', value: `${avgActivities} / 天`, hint: `累计 ${activityCount} 个行程节点` },
    { label: '预算状态', value: withinBudget ? '可控' : '偏紧', hint: '来自 Budget Agent 评估' },
    { label: '风险数量', value: `${props.result?.warnings.length ?? 0} 条`, hint: '天气 / 预算 / 节奏相关提醒' },
  ]
})

const riskForecasts = computed(() => {
  const forecasts = props.result?.domain_insights?.risk?.structured_data?.forecasts
  return Array.isArray(forecasts)
    ? (forecasts as Array<Record<string, string | number | Record<string, number>>>)
    : []
})

const confidenceBoard = computed(() =>
  insightEntries.value.map(([, insight]) => ({
    agentType: insight.agent_type,
    confidence: Math.round((insight.confidence_score ?? 0) * 100),
  })),
)

const toolSummaries = computed(() =>
  insightEntries.value.flatMap(([, insight]) => insight.tool_summaries ?? []).slice(0, 6),
)

function currency(value: number) {
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY',
    maximumFractionDigits: 0,
  }).format(value)
}

function labelBudget(key: string) {
  const dictionary: Record<string, string> = {
    transport: '大交通',
    hotel: '住宿',
    tickets: '门票',
    food: '餐饮',
    local_transport: '市内交通',
    buffer: '机动金',
  }
  return dictionary[key] ?? key
}

const exportSummary = computed(() => {
  if (!props.result) {
    return ''
  }

  const dayLines = props.result.days.map(
    (day) => `Day ${day.day_index}｜${day.city}｜${day.theme}｜${day.items.map((item) => `${item.time} ${item.title}`).join(' / ')}`,
  )
  const warningLines = props.result.warnings.length ? props.result.warnings.join('；') : '无高优先级风险'

  return [
    `规划摘要：${props.result.summary}`,
    `总预算：${currency(budgetTotal.value)}`,
    `行程天数：${props.result.days.length} 天`,
    `风险提醒：${warningLines}`,
    ...dayLines,
  ].join('\n')
})

async function handleCopySummary() {
  if (!exportSummary.value) {
    return
  }

  try {
    await navigator.clipboard.writeText(exportSummary.value)
    copyStatus.value = '已复制'
  } catch {
    copyStatus.value = '复制失败'
  }

  window.setTimeout(() => {
    copyStatus.value = '复制摘要'
  }, 1800)
}
</script>

<template>
  <section class="result-panel glass-panel">
    <div class="result-header">
      <div>
        <span class="panel-kicker">Final Deliverable</span>
        <h3>规划成品总览</h3>
        <p v-if="result">{{ result.summary }}</p>
        <p v-else>当规划完成后，这里会展示日程成品、预算、风险、候选方案与协同洞察。</p>
      </div>
      <div v-if="result" class="header-actions">
        <button class="secondary-button" @click="handleCopySummary">{{ copyStatus }}</button>
        <button class="secondary-button" @click="emit('replan')">预算收紧重规划</button>
      </div>
    </div>

    <div v-if="result" class="result-content">
      <div class="stats-grid">
        <article class="surface-card stat-card">
          <span>行程天数</span>
          <strong>{{ result.days.length }} 天</strong>
        </article>
        <article class="surface-card stat-card">
          <span>预算总额</span>
          <strong>{{ currency(budgetTotal) }}</strong>
        </article>
        <article class="surface-card stat-card">
          <span>风险提醒</span>
          <strong>{{ result.warnings.length }} 条</strong>
        </article>
        <article class="surface-card stat-card">
          <span>备选预案</span>
          <strong>{{ result.fallback_plans.length }} 条</strong>
        </article>
      </div>

      <section class="section-block">
        <div class="section-heading">
          <h4>路线地图视图</h4>
          <span>基于现有结果数据生成路线与城市停靠分析</span>
        </div>
        <div class="map-layout">
          <article class="surface-card map-card">
            <div class="map-card__top">
              <div>
                <strong>多城市路线概览</strong>
                <small>用规划结果中的城市节点、顺序和主题生成空间示意</small>
              </div>
              <span class="map-badge">{{ result.days.length }} 个规划节点</span>
            </div>

            <div class="map-canvas">
              <div class="map-canvas__glow"></div>
              <svg class="map-path" viewBox="0 0 100 100" preserveAspectRatio="none">
                <polyline :points="mapPolyline" />
              </svg>
              <div
                v-for="stop in mapStops"
                :key="`${stop.label}-${stop.city}`"
                class="map-stop"
                :style="{ left: `${stop.x}%`, top: `${stop.y}%` }"
              >
                <span class="map-stop__pin"></span>
                <div class="map-stop__label">
                  <strong>{{ stop.label }}</strong>
                  <span>{{ stop.city }}</span>
                </div>
              </div>
            </div>
          </article>

          <article class="surface-card route-card">
            <div class="section-heading compact">
              <h4>路线分析</h4>
              <span>Result Navigator</span>
            </div>

            <ul class="route-list">
              <li v-for="item in routeSummary" :key="item">
                <span class="route-list__dot"></span>
                <span>{{ item }}</span>
              </li>
            </ul>

            <div class="route-signal-grid">
              <article v-for="stat in routeStats" :key="stat.label" class="route-signal">
                <span>{{ stat.label }}</span>
                <strong>{{ stat.value }}</strong>
                <small>{{ stat.hint }}</small>
              </article>
            </div>

            <div v-if="riskForecasts.length" class="forecast-stack">
              <strong>天气与稳定性</strong>
              <div class="forecast-list">
                <article v-for="forecast in riskForecasts" :key="`${forecast.city}-${forecast.date}`" class="forecast-card">
                  <div>
                    <strong>{{ forecast.city }}</strong>
                    <span>{{ forecast.condition }}</span>
                  </div>
                  <small>{{ forecast.advice }}</small>
                </article>
              </div>
            </div>

            <div v-if="toolSummaries.length" class="tool-summary-stack">
              <strong>工具摘要</strong>
              <ul class="bullet-list compact-list">
                <li v-for="item in toolSummaries" :key="item">{{ item }}</li>
              </ul>
            </div>
          </article>
        </div>
      </section>

      <section class="section-block">
        <div class="section-heading">
          <h4>每日时间轴</h4>
          <span>按城市、主题和时间节奏组织结果</span>
        </div>
        <div class="timeline-grid">
          <article v-for="day in result.days" :key="`${day.date}-${day.day_index}`" class="timeline-card surface-card">
            <div class="timeline-top">
              <div>
                <span class="timeline-index">Day {{ day.day_index }}</span>
                <h5>{{ day.city }} · {{ day.theme }}</h5>
              </div>
              <span class="timeline-date">{{ day.date }}</span>
            </div>

            <ul class="day-items">
              <li v-for="item in day.items" :key="`${day.date}-${item.time}-${item.title}`">
                <strong>{{ item.time }}</strong>
                <div>
                  <span>{{ item.title }}</span>
                  <small>{{ item.description }}</small>
                </div>
              </li>
            </ul>

            <div class="day-footnotes">
              <div>住宿建议：{{ day.hotel_tip }}</div>
              <div>交通建议：{{ day.transport_tip }}</div>
            </div>
          </article>
        </div>
      </section>

      <div class="matrix-grid">
        <section class="surface-card side-card">
          <div class="section-heading compact">
            <h4>预算拆分</h4>
            <span>费用结构</span>
          </div>
          <ul class="kv-list">
            <li v-for="([key, value]) in budgetItems" :key="key">
              <span>{{ labelBudget(key) }}</span>
              <strong>{{ currency(Number(value)) }}</strong>
            </li>
          </ul>
          <div class="budget-bars">
            <div v-for="bar in budgetBars" :key="bar.key" class="budget-bar">
              <div class="budget-bar__meta">
                <span>{{ labelBudget(bar.key) }}</span>
                <small>{{ Math.round(bar.percent) }}%</small>
              </div>
              <div class="budget-bar__track">
                <div class="budget-bar__fill" :style="{ width: `${bar.percent}%` }"></div>
              </div>
            </div>
          </div>
        </section>

        <section class="surface-card side-card">
          <div class="section-heading compact">
            <h4>风险与预案</h4>
            <span>风险闭环</span>
          </div>
          <ul class="bullet-list">
            <li v-for="warning in result.warnings" :key="warning">{{ warning }}</li>
            <li v-if="!result.warnings.length">当前无高优先级风险。</li>
          </ul>
          <div class="divider"></div>
          <ul class="bullet-list muted">
            <li v-for="fallback in result.fallback_plans" :key="fallback">{{ fallback }}</li>
          </ul>
        </section>
      </div>

      <div class="matrix-grid">
        <section class="surface-card side-card">
          <div class="section-heading compact">
            <h4>交通候选</h4>
            <span>外部工具融合结果</span>
          </div>
          <ul class="option-list">
            <li v-for="option in result.transport_options" :key="`${option.mode}-${option.depart_time}`">
              <strong>{{ option.mode }}</strong>
              <span>{{ option.depart_time }} - {{ option.arrive_time }}</span>
              <small>{{ option.duration_minutes }} 分钟 · ¥{{ option.price }}</small>
            </li>
          </ul>
        </section>

        <section class="surface-card side-card">
          <div class="section-heading compact">
            <h4>住宿候选</h4>
            <span>区域与价格平衡</span>
          </div>
          <ul class="option-list">
            <li v-for="hotel in result.hotel_options" :key="`${hotel.name}-${hotel.district}`">
              <strong>{{ hotel.name }}</strong>
              <span>{{ hotel.district }}</span>
              <small>评分 {{ hotel.rating }} · 总价 ¥{{ hotel.stay_total }}</small>
            </li>
          </ul>
        </section>
      </div>

      <section v-if="insightEntries.length" class="section-block">
        <div class="section-heading">
          <h4>协同洞察</h4>
          <span>展示各领域 Agent 的结论摘要与亮点</span>
        </div>

        <div class="confidence-board">
          <article v-for="item in confidenceBoard" :key="item.agentType" class="surface-card confidence-card">
            <div class="confidence-card__meta">
              <strong>{{ item.agentType }}</strong>
              <span>{{ item.confidence }}%</span>
            </div>
            <div class="confidence-track">
              <div class="confidence-fill" :style="{ width: `${item.confidence}%` }"></div>
            </div>
          </article>
        </div>

        <div class="insight-grid">
          <article v-for="([key, insight]) in insightEntries" :key="key" class="surface-card insight-card">
            <div class="insight-top">
              <strong>{{ insight.agent_type }}</strong>
              <span>置信度 {{ Math.round((insight.confidence_score ?? 0) * 100) }}%</span>
            </div>
            <p>{{ insight.summary }}</p>
            <ul class="bullet-list compact-list">
              <li v-for="item in insight.highlights" :key="item">{{ item }}</li>
            </ul>
          </article>
        </div>
      </section>
    </div>

    <div v-else class="empty-state surface-card">
      <strong>等待规划结果</strong>
      <p>专业版结果工作台会在规划完成后自动填充日程时间轴、预算矩阵、风险闭环和 Agent 洞察。</p>
    </div>
  </section>
</template>

<style scoped>
.result-panel {
  display: grid;
  gap: 18px;
}

.result-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
}

.header-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.panel-kicker {
  color: var(--accent);
  font-size: 12px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.result-header h3 {
  margin: 6px 0 8px;
  font-size: 24px;
}

.result-header p {
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.7;
}

.secondary-button {
  border: 1px solid rgba(var(--accent-rgb), 0.26);
  background: rgba(var(--accent-rgb), 0.1);
  color: var(--accent-strong);
  border-radius: 16px;
  padding: 12px 16px;
  cursor: pointer;
}

.result-content,
.section-block {
  display: grid;
  gap: 16px;
}

.stats-grid,
.matrix-grid,
.insight-grid,
.map-layout {
  display: grid;
  gap: 14px;
}

.stats-grid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.matrix-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.map-layout {
  grid-template-columns: minmax(0, 1.15fr) minmax(260px, 0.85fr);
}

.insight-grid,
.timeline-grid {
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  display: grid;
  gap: 14px;
}

.stat-card {
  display: grid;
  gap: 8px;
}

.stat-card span {
  font-size: 12px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.stat-card strong {
  font-size: 22px;
}

.section-heading {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: baseline;
}

.section-heading.compact {
  align-items: center;
}

.section-heading h4 {
  margin: 0;
  font-size: 18px;
}

.section-heading span {
  color: var(--text-muted);
  font-size: 13px;
}

.timeline-card,
.map-card,
.route-card,
.side-card,
.insight-card {
  display: grid;
  gap: 14px;
}

.map-card__top {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
}

.map-card__top strong {
  display: block;
  font-size: 18px;
}

.map-card__top small {
  color: var(--text-muted);
}

.map-badge {
  display: inline-flex;
  align-items: center;
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(var(--accent-rgb), 0.12);
  color: var(--accent-strong);
  font-size: 12px;
}

.map-canvas {
  position: relative;
  min-height: 320px;
  overflow: hidden;
  border-radius: 22px;
  background:
    linear-gradient(180deg, rgba(var(--accent-rgb), 0.08), transparent 36%),
    linear-gradient(0deg, rgba(var(--accent-rgb), 0.06), transparent 26%),
    var(--surface-strong);
  border: 1px solid var(--border-color);
}

.map-canvas::before,
.map-canvas::after {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.map-canvas::before {
  background-image:
    linear-gradient(to right, rgba(var(--accent-rgb), 0.06) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(var(--accent-rgb), 0.06) 1px, transparent 1px);
  background-size: 44px 44px;
  opacity: 0.7;
}

.map-canvas::after {
  background: radial-gradient(circle at 50% 48%, rgba(var(--accent-rgb), 0.12), transparent 34%);
}

.map-canvas__glow {
  position: absolute;
  inset: auto 10% 18% auto;
  width: 240px;
  height: 240px;
  border-radius: 999px;
  background: rgba(var(--accent-rgb), 0.14);
  filter: blur(36px);
}

.map-path {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.map-path polyline {
  fill: none;
  stroke: var(--accent);
  stroke-width: 1.6;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-dasharray: 3 2;
  opacity: 0.8;
}

.map-stop {
  position: absolute;
  transform: translate(-50%, -50%);
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.map-stop__pin {
  width: 14px;
  height: 14px;
  border-radius: 999px;
  background: var(--accent);
  box-shadow: 0 0 0 6px rgba(var(--accent-rgb), 0.14);
}

.map-stop__label {
  display: grid;
  gap: 2px;
  min-width: 78px;
  padding: 8px 10px;
  border-radius: 14px;
  background: rgba(10, 18, 32, 0.78);
  border: 1px solid rgba(var(--accent-rgb), 0.18);
  text-align: center;
}

:global(html[data-theme='light']) .map-stop__label {
  background: rgba(255, 255, 255, 0.92);
}

.map-stop__label strong {
  font-size: 12px;
  color: var(--accent-strong);
}

.map-stop__label span {
  font-size: 12px;
  color: var(--text-secondary);
}

.route-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 10px;
}

.route-list li {
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--text-secondary);
}

.route-list__dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: var(--accent);
  box-shadow: 0 0 0 5px rgba(var(--accent-rgb), 0.12);
}

.route-signal-grid,
.forecast-list,
.confidence-board {
  display: grid;
  gap: 12px;
}

.route-signal-grid,
.confidence-board {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.route-signal,
.forecast-card,
.confidence-card {
  display: grid;
  gap: 8px;
  padding: 14px;
  border-radius: 18px;
  background: var(--surface-strong);
  border: 1px solid var(--border-color);
}

.route-signal span,
.forecast-card span {
  color: var(--text-muted);
  font-size: 12px;
}

.route-signal strong,
.forecast-card strong {
  font-size: 18px;
}

.route-signal small,
.forecast-card small {
  color: var(--text-secondary);
  line-height: 1.6;
}

.forecast-stack,
.tool-summary-stack {
  display: grid;
  gap: 12px;
}

.confidence-card__meta {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  align-items: center;
}

.confidence-track {
  width: 100%;
  height: 10px;
  border-radius: 999px;
  background: rgba(var(--accent-rgb), 0.1);
  overflow: hidden;
}

.confidence-fill {
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(135deg, var(--accent), var(--accent-strong));
}

.timeline-top {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
}

.timeline-index {
  display: inline-flex;
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(var(--accent-rgb), 0.12);
  color: var(--accent-strong);
  font-size: 12px;
  margin-bottom: 10px;
}

.timeline-top h5 {
  margin: 0;
  font-size: 20px;
}

.timeline-date {
  color: var(--text-faint);
  font-size: 13px;
}

.day-items,
.kv-list,
.bullet-list,
.option-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 10px;
}

.day-items li {
  display: grid;
  grid-template-columns: 100px minmax(0, 1fr);
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px dashed var(--border-color);
}

.day-items li:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.day-items div,
.option-list li {
  display: grid;
  gap: 4px;
}

.day-items small,
.option-list small,
.insight-card p,
.day-footnotes,
.bullet-list.muted,
.kv-list span {
  color: var(--text-secondary);
}

.day-footnotes {
  display: grid;
  gap: 8px;
  font-size: 14px;
}

.kv-list li {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  align-items: center;
}

.budget-bars {
  display: grid;
  gap: 10px;
}

.budget-bar {
  display: grid;
  gap: 6px;
}

.budget-bar__meta {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  align-items: center;
  color: var(--text-secondary);
  font-size: 13px;
}

.budget-bar__track {
  width: 100%;
  height: 9px;
  border-radius: 999px;
  background: var(--surface-strong);
  overflow: hidden;
  border: 1px solid var(--border-color);
}

.budget-bar__fill {
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, var(--accent), var(--accent-strong));
  box-shadow: 0 0 18px rgba(var(--accent-rgb), 0.28);
}

.divider {
  height: 1px;
  background: var(--border-color);
}

.insight-top {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  align-items: center;
}

.insight-top span {
  color: var(--text-muted);
  font-size: 12px;
}

.insight-card p {
  margin: 0;
  line-height: 1.7;
}

.compact-list {
  gap: 8px;
}

.empty-state {
  display: grid;
  gap: 8px;
}

.empty-state strong,
.empty-state p {
  margin: 0;
}

.empty-state p {
  color: var(--text-secondary);
  line-height: 1.7;
}

@media (max-width: 980px) {
  .result-header,
  .section-heading,
  .timeline-top {
    flex-direction: column;
    align-items: flex-start;
  }

  .stats-grid,
  .matrix-grid,
  .map-layout {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .route-signal-grid,
  .confidence-board {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .stats-grid,
  .matrix-grid,
  .map-layout,
  .insight-grid,
  .timeline-grid {
    grid-template-columns: 1fr;
  }

  .day-items li {
    grid-template-columns: 1fr;
  }
}
</style>
