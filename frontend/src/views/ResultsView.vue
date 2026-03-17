<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink } from 'vue-router'

import PlanResultPanel from '../components/PlanResult.vue'
import { useWorkspace } from '../composables/useWorkspace'

const {
  result,
  currentStatus,
  handleReplan,
} = useWorkspace()

const resultMetrics = computed(() => {
  if (!result.value) {
    return [
      { label: '行程天数', value: '--' },
      { label: '预算总额', value: '--' },
      { label: '风险提醒', value: '--' },
      { label: '备选预案', value: '--' },
    ]
  }

  const budget = Object.values(result.value.budget_breakdown ?? {}).reduce((sum, value) => sum + Number(value || 0), 0)
  return [
    { label: '行程天数', value: `${result.value.days.length} 天` },
    { label: '预算总额', value: `¥${Math.round(budget)}` },
    { label: '风险提醒', value: `${result.value.warnings.length} 条` },
    { label: '备选预案', value: `${result.value.fallback_plans.length} 条` },
  ]
})
</script>

<template>
  <section class="portal-page">
    <section class="glass-panel hero-panel">
      <div>
        <span class="eyebrow">Deliverable Portal</span>
        <h1>结果资产</h1>
        <p>把规划结果视为可浏览的内容资产：路线、预算、时间轴、候选方案和协同洞察都在这里统一消费。</p>
      </div>

      <div class="hero-actions">
        <span class="status-pill">{{ currentStatus }}</span>
        <RouterLink class="nav-chip" :to="{ name: 'overview' }">回到首页</RouterLink>
      </div>
    </section>

    <section class="metric-strip">
      <article v-for="metric in resultMetrics" :key="metric.label" class="surface-card metric-card">
        <span>{{ metric.label }}</span>
        <strong>{{ metric.value }}</strong>
      </article>
    </section>

    <PlanResultPanel :result="result" @replan="handleReplan" />
  </section>
</template>

<style scoped>
.portal-page,
.metric-strip {
  display: grid;
  gap: 18px;
}

.hero-panel,
.hero-actions {
  display: flex;
}

.hero-panel {
  justify-content: space-between;
  gap: 18px;
  align-items: flex-start;
}

.eyebrow {
  display: inline-flex;
  color: var(--accent);
  text-transform: uppercase;
  letter-spacing: 0.14em;
  font-size: 12px;
}

.hero-panel h1,
.hero-panel p,
.metric-card strong,
.metric-card span {
  margin: 0;
}

.hero-panel h1 {
  margin-top: 6px;
  font-size: clamp(34px, 4vw, 48px);
}

.hero-panel p,
.metric-card span {
  color: var(--text-secondary);
  line-height: 1.8;
}

.hero-actions {
  gap: 10px;
  flex-wrap: wrap;
}

.status-pill,
.nav-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 10px 14px;
  border-radius: 999px;
  font-size: 12px;
  border: 1px solid rgba(var(--accent-rgb), 0.2);
  background: rgba(var(--accent-rgb), 0.08);
  color: var(--accent-strong);
  text-decoration: none;
}

.metric-strip {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.metric-card {
  display: grid;
  gap: 8px;
}

.metric-card strong {
  font-size: 26px;
}

@media (max-width: 1024px) {
  .metric-strip {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .hero-panel {
    flex-direction: column;
  }

  .metric-strip {
    grid-template-columns: 1fr;
  }
}
</style>
