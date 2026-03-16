<script setup lang="ts">
import { computed } from 'vue'

import type { PlanEvent } from '../types'

const props = defineProps<{
  events: PlanEvent[]
  loading: boolean
}>()

const metrics = computed(() => {
  const agentCount = new Set(
    props.events
      .map((event) => String(event.data?.agent_type ?? ''))
      .filter(Boolean),
  ).size
  const toolCount = props.events.filter((event) => event.type.includes('tool')).length
  const lastStage = props.events.at(-1)?.type ?? '等待触发'
  return [
    { label: '事件数', value: `${props.events.length}` },
    { label: 'Agent 活跃数', value: `${agentCount}` },
    { label: '工具调用', value: `${toolCount}` },
    { label: '最近阶段', value: lastStage },
  ]
})

function labelForEvent(type: string) {
  if (type === 'plan_started') return '启动'
  if (type === 'task_dispatched') return '分发'
  if (type === 'agent_progress') return '执行'
  if (type === 'replan_triggered') return '重规划'
  if (type === 'plan_completed') return '完成'
  if (type === 'plan_failed') return '失败'
  return type
}

function extractChips(data: Record<string, unknown>) {
  return Object.entries(data)
    .filter(([, value]) => ['string', 'number', 'boolean'].includes(typeof value))
    .slice(0, 3)
}
</script>

<template>
  <section class="stream-panel glass-panel">
    <div class="stream-header">
      <div>
        <span class="panel-kicker">Execution Trace</span>
        <h3>多 Agent 协同过程</h3>
        <p>实时查看 Parent Agent 如何拆解任务、调度子 Agent、聚合结果并触发重规划。</p>
      </div>
      <span :class="['status-pill', loading ? 'running' : 'completed']">{{ loading ? '运行中' : '已完成' }}</span>
    </div>

    <div class="metrics-row">
      <article v-for="metric in metrics" :key="metric.label" class="surface-card metric-item">
        <span>{{ metric.label }}</span>
        <strong>{{ metric.value }}</strong>
      </article>
    </div>

    <div class="timeline">
      <article v-for="event in events" :key="`${event.timestamp}-${event.message}`" class="event-card">
        <div class="event-rail"></div>
        <div class="event-body">
          <div class="event-topline">
            <span class="event-tag">{{ labelForEvent(event.type) }}</span>
            <span class="event-time">{{ new Date(event.timestamp).toLocaleString() }}</span>
          </div>
          <div class="event-message">{{ event.message }}</div>
          <div v-if="extractChips(event.data).length" class="event-chip-row">
            <span
              v-for="([key, value]) in extractChips(event.data)"
              :key="`${event.timestamp}-${key}`"
              class="event-chip"
            >
              {{ key }}: {{ value }}
            </span>
          </div>
          <pre v-if="Object.keys(event.data).length" class="event-data">{{ JSON.stringify(event.data, null, 2) }}</pre>
        </div>
      </article>

      <div v-if="!events.length" class="empty-state surface-card">
        <strong>等待规划任务</strong>
        <p>提交规划后，这里会以专业时间轴视图展示 Parent Agent 和 6 个领域 Agent 的工作轨迹。</p>
      </div>
    </div>
  </section>
</template>

<style scoped>
.stream-panel {
  display: grid;
  gap: 18px;
}

.stream-header {
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

.stream-header h3 {
  margin: 6px 0 8px;
  font-size: 24px;
}

.stream-header p {
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.7;
}

.status-pill {
  display: inline-flex;
  padding: 10px 14px;
  border-radius: 999px;
  font-size: 13px;
  border: 1px solid var(--border-color);
}

.status-pill.running {
  background: rgba(var(--accent-rgb), 0.12);
  color: var(--accent-strong);
  border-color: rgba(var(--accent-rgb), 0.24);
}

.status-pill.completed {
  background: rgba(var(--success-rgb), 0.12);
  color: var(--success);
  border-color: rgba(var(--success-rgb), 0.24);
}

.metrics-row {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.metric-item {
  display: grid;
  gap: 10px;
}

.metric-item span {
  color: var(--text-muted);
  font-size: 12px;
}

.metric-item strong {
  font-size: 20px;
}

.timeline {
  display: grid;
  gap: 14px;
}

.event-card {
  display: grid;
  grid-template-columns: 18px minmax(0, 1fr);
  gap: 14px;
  align-items: stretch;
}

.event-rail {
  position: relative;
}

.event-rail::before {
  content: '';
  position: absolute;
  top: 6px;
  left: 7px;
  width: 4px;
  height: calc(100% - 6px);
  border-radius: 999px;
  background: linear-gradient(180deg, var(--accent), rgba(var(--accent-rgb), 0.06));
}

.event-rail::after {
  content: '';
  position: absolute;
  top: 8px;
  left: 2px;
  width: 14px;
  height: 14px;
  border-radius: 999px;
  background: var(--accent);
  box-shadow: 0 0 0 6px rgba(var(--accent-rgb), 0.12);
}

.event-body {
  background: var(--surface-muted);
  border: 1px solid var(--border-color);
  border-radius: 18px;
  padding: 16px;
}

.event-topline {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
  margin-bottom: 10px;
}

.event-tag {
  display: inline-flex;
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(var(--accent-rgb), 0.12);
  color: var(--accent-strong);
  font-size: 12px;
}

.event-time {
  color: var(--text-faint);
  font-size: 12px;
}

.event-message {
  font-size: 16px;
  font-weight: 700;
}

.event-chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.event-chip {
  padding: 8px 10px;
  border-radius: 999px;
  background: var(--surface-strong);
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
  font-size: 12px;
}

.event-data {
  margin: 12px 0 0;
  padding: 12px;
  border-radius: 14px;
  background: rgba(0, 0, 0, 0.12);
  color: var(--text-muted);
  white-space: pre-wrap;
}

.empty-state {
  display: grid;
  gap: 8px;
}

.empty-state p,
.empty-state strong {
  margin: 0;
}

.empty-state p {
  color: var(--text-secondary);
  line-height: 1.7;
}

@media (max-width: 860px) {
  .stream-header {
    flex-direction: column;
  }

  .metrics-row {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 560px) {
  .metrics-row {
    grid-template-columns: 1fr;
  }

  .event-topline {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
