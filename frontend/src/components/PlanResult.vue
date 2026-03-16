<script setup lang="ts">
import { computed } from 'vue'

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
const budgetBars = computed(() =>
  budgetItems.value.map(([key, value]) => ({
    key,
    value: Number(value),
    percent: budgetTotal.value ? Math.max(8, (Number(value) / budgetTotal.value) * 100) : 0,
  })),
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
      <button v-if="result" class="secondary-button" @click="emit('replan')">预算收紧重规划</button>
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
.insight-grid {
  display: grid;
  gap: 14px;
}

.stats-grid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.matrix-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
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
.side-card,
.insight-card {
  display: grid;
  gap: 14px;
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
  .matrix-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .stats-grid,
  .matrix-grid,
  .insight-grid,
  .timeline-grid {
    grid-template-columns: 1fr;
  }

  .day-items li {
    grid-template-columns: 1fr;
  }
}
</style>
