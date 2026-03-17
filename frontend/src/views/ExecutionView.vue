<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink } from 'vue-router'

import PlanningStream from '../components/PlanningStream.vue'
import { useWorkspace } from '../composables/useWorkspace'

const {
  loading,
  events,
  currentStatus,
  workspaceStages,
} = useWorkspace()

const executionMetrics = computed(() => {
  const eventTypes = events.value.map((event) => event.type)
  return [
    { label: '事件总数', value: `${events.value.length} 条`, hint: '规划全程实时事件流' },
    { label: '阶段完成', value: `${workspaceStages.value.filter((stage) => stage.done).length}/${workspaceStages.value.length}`, hint: '当前协作阶段进度' },
    { label: 'Agent 回执', value: `${eventTypes.filter((type) => type === 'agent_progress').length} 次`, hint: '领域 Agent 返回次数' },
    { label: '自动重规划', value: `${eventTypes.filter((type) => type === 'replan_triggered').length} 次`, hint: '质量闸门触发情况' },
  ]
})
</script>

<template>
  <section class="portal-page">
    <section class="glass-panel hero-panel">
      <div>
        <span class="eyebrow">Execution Portal</span>
        <h1>执行轨迹</h1>
        <p>以门户式布局展示 Parent Agent 的调度节奏、领域 Agent 回执、关键事件和重规划触发点。</p>
      </div>

      <div class="hero-actions">
        <span class="status-pill">{{ currentStatus }}</span>
        <RouterLink class="nav-chip" :to="{ name: 'results' }">查看结果资产</RouterLink>
      </div>
    </section>

    <section class="metric-strip">
      <article v-for="metric in executionMetrics" :key="metric.label" class="surface-card metric-card">
        <span>{{ metric.label }}</span>
        <strong>{{ metric.value }}</strong>
        <small>{{ metric.hint }}</small>
      </article>
    </section>

    <section class="portal-grid">
      <section class="surface-card stage-panel">
        <div class="section-heading">
          <div>
            <span class="eyebrow">Progress Rail</span>
            <h2>协作阶段</h2>
          </div>
        </div>

        <div class="stage-rail">
          <article
            v-for="stage in workspaceStages"
            :key="stage.label"
            :class="['stage-chip', { active: stage.active, done: stage.done }]"
          >
            <span class="stage-dot"></span>
            <span>{{ stage.label }}</span>
          </article>
        </div>
      </section>

      <section class="surface-card tips-panel">
        <div class="section-heading">
          <div>
            <span class="eyebrow">Operator Tips</span>
            <h2>观测建议</h2>
          </div>
        </div>

        <ul class="tip-list">
          <li>重点关注 `replan_triggered` 事件，判断预算或天气是否导致方案反复调整。</li>
          <li>若 Agent 回执数量明显不足，优先检查模型配置和后端服务状态。</li>
          <li>完成后可跳转结果页查看预算、路线强度和最终成品资产。</li>
        </ul>
      </section>
    </section>

    <PlanningStream :events="events" :loading="loading" />
  </section>
</template>

<style scoped>
.portal-page,
.metric-strip,
.portal-grid,
.stage-panel,
.tips-panel {
  display: grid;
  gap: 18px;
}

.hero-panel,
.hero-actions,
.section-heading {
  display: flex;
}

.hero-panel,
.section-heading {
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
.section-heading h2,
.hero-panel p,
.metric-card small,
.tip-list {
  margin: 0;
}

.hero-panel h1 {
  font-size: clamp(34px, 4vw, 48px);
  margin-top: 6px;
}

.hero-panel p,
.metric-card small,
.tip-list {
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

.metric-card span {
  color: var(--text-muted);
  font-size: 12px;
}

.metric-card strong {
  font-size: 26px;
}

.portal-grid {
  grid-template-columns: minmax(0, 1.2fr) 320px;
}

.stage-rail {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 12px;
}

.stage-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 52px;
  border-radius: 18px;
  background: var(--surface-strong);
  border: 1px solid var(--border-color);
  color: var(--text-muted);
}

.stage-chip.active {
  color: var(--accent-strong);
  border-color: rgba(var(--accent-rgb), 0.2);
  background: rgba(var(--accent-rgb), 0.08);
}

.stage-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: currentColor;
}

.tip-list {
  padding-left: 18px;
}

.tip-list li + li {
  margin-top: 10px;
}

@media (max-width: 1200px) {
  .metric-strip,
  .portal-grid,
  .stage-rail {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .hero-panel,
  .section-heading {
    flex-direction: column;
  }

  .metric-strip,
  .portal-grid,
  .stage-rail {
    grid-template-columns: 1fr;
  }
}
</style>
