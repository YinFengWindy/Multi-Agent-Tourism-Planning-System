<script setup lang="ts">
import { computed, reactive } from 'vue'

import type { PlanRequest } from '../types'

const emit = defineEmits<{
  submit: [payload: PlanRequest]
}>()

const form = reactive({
  originCity: '上海',
  destinations: '杭州,乌镇',
  startDate: '2026-05-01',
  endDate: '2026-05-03',
  travelers: 2,
  budget: 4200,
  preferences: '美食,古镇,轻松节奏',
  hotelLevel: '舒适型',
  transportMode: '高铁,地铁,打车',
  dailyStartAfter: '09:00',
  dailyEndBefore: '21:30',
})

const destinationPreview = computed(() =>
  form.destinations
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean),
)

const preferencePreview = computed(() =>
  form.preferences
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean),
)

const tripDays = computed(() => {
  const start = new Date(form.startDate)
  const end = new Date(form.endDate)
  if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) {
    return '--'
  }
  const diff = Math.max(1, Math.round((end.getTime() - start.getTime()) / 86400000) + 1)
  return `${diff} 天`
})

function handleSubmit() {
  emit('submit', {
    origin_city: form.originCity,
    destination_cities: destinationPreview.value,
    start_date: form.startDate,
    end_date: form.endDate,
    travelers: Number(form.travelers),
    budget: Number(form.budget),
    preferences: preferencePreview.value,
    constraints: {
      transport_mode: form.transportMode.split(',').map((item) => item.trim()).filter(Boolean),
      hotel_level: form.hotelLevel,
      daily_start_after: form.dailyStartAfter,
      daily_end_before: form.dailyEndBefore,
      budget_mode: 'balanced',
    },
  })
}
</script>

<template>
  <section class="planner-panel glass-panel">
    <div class="panel-topbar">
      <div>
        <span class="panel-kicker">Planning Input</span>
        <h2>旅行约束配置器</h2>
        <p>像操作专业业务工作台一样组织需求、约束与偏好，再交给 Parent Agent 编排。</p>
      </div>
      <button class="primary-button" @click="handleSubmit">发起规划</button>
    </div>

    <div class="planner-layout">
      <div class="form-sections">
        <section class="surface-card form-section">
          <div class="section-title">基础行程</div>
          <div class="field-grid">
            <label>
              出发城市
              <input v-model="form.originCity" />
            </label>
            <label>
              目的地城市
              <input v-model="form.destinations" placeholder="杭州,乌镇" />
            </label>
            <label>
              开始日期
              <input v-model="form.startDate" type="date" />
            </label>
            <label>
              结束日期
              <input v-model="form.endDate" type="date" />
            </label>
            <label>
              出行人数
              <input v-model="form.travelers" type="number" min="1" />
            </label>
            <label>
              总预算
              <input v-model="form.budget" type="number" min="500" step="100" />
            </label>
          </div>
        </section>

        <section class="surface-card form-section">
          <div class="section-title">偏好与资源策略</div>
          <div class="field-grid">
            <label>
              偏好标签
              <input v-model="form.preferences" placeholder="美食,古镇,城市漫步" />
            </label>
            <label>
              交通偏好
              <input v-model="form.transportMode" placeholder="高铁,地铁,打车" />
            </label>
            <label>
              酒店档位
              <select v-model="form.hotelLevel">
                <option>经济型</option>
                <option>舒适型</option>
                <option>高端型</option>
              </select>
            </label>
          </div>
        </section>

        <section class="surface-card form-section">
          <div class="section-title">每日节奏约束</div>
          <div class="field-grid compact-grid">
            <label>
              每日开始时间
              <input v-model="form.dailyStartAfter" type="time" />
            </label>
            <label>
              每日结束时间
              <input v-model="form.dailyEndBefore" type="time" />
            </label>
          </div>
        </section>
      </div>

      <aside class="summary-column">
        <section class="surface-card insight-card">
          <span class="summary-label">本次行程画像</span>
          <strong class="summary-number">{{ tripDays }}</strong>
          <small>系统会自动按日期推导天数，并将城市与预算映射到多 Agent 协同任务图。</small>
        </section>

        <section class="surface-card chip-card">
          <div class="chip-group-title">目的地</div>
          <div class="chip-wrap">
            <span v-for="item in destinationPreview" :key="item" class="info-chip">{{ item }}</span>
          </div>
        </section>

        <section class="surface-card chip-card">
          <div class="chip-group-title">用户偏好</div>
          <div class="chip-wrap">
            <span v-for="item in preferencePreview" :key="item" class="info-chip soft">{{ item }}</span>
          </div>
        </section>
      </aside>
    </div>
  </section>
</template>

<style scoped>
.planner-panel {
  display: grid;
  gap: 20px;
}

.panel-topbar {
  display: flex;
  justify-content: space-between;
  gap: 18px;
  align-items: flex-start;
}

.panel-kicker {
  color: var(--accent);
  font-size: 12px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.panel-topbar h2 {
  margin: 6px 0 8px;
  font-size: 30px;
}

.panel-topbar p {
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.7;
}

.primary-button {
  border: none;
  border-radius: 16px;
  padding: 13px 18px;
  background: linear-gradient(135deg, var(--accent), var(--accent-strong));
  color: var(--accent-contrast);
  cursor: pointer;
  box-shadow: 0 14px 28px rgba(var(--accent-rgb), 0.24);
}

.planner-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(260px, 320px);
  gap: 18px;
}

.form-sections,
.summary-column {
  display: grid;
  gap: 16px;
}

.form-section {
  display: grid;
  gap: 14px;
}

.section-title {
  font-size: 16px;
  font-weight: 700;
}

.field-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.compact-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

label {
  display: grid;
  gap: 8px;
  color: var(--text-secondary);
  font-size: 14px;
}

input,
select {
  border: 1px solid var(--border-color);
  background: var(--surface-strong);
  color: var(--text-primary);
  border-radius: 14px;
  padding: 12px 14px;
}

.insight-card {
  display: grid;
  gap: 10px;
}

.summary-label,
.chip-group-title {
  color: var(--text-muted);
  font-size: 13px;
}

.summary-number {
  font-size: 36px;
}

.insight-card small {
  color: var(--text-secondary);
  line-height: 1.7;
}

.chip-card {
  display: grid;
  gap: 12px;
}

.chip-wrap {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.info-chip {
  padding: 10px 14px;
  border-radius: 999px;
  background: rgba(var(--accent-rgb), 0.12);
  border: 1px solid rgba(var(--accent-rgb), 0.18);
  color: var(--accent-strong);
  font-size: 13px;
}

.info-chip.soft {
  background: var(--surface-muted);
  color: var(--text-secondary);
}

@media (max-width: 1120px) {
  .planner-layout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .panel-topbar {
    flex-direction: column;
  }

  .field-grid,
  .compact-grid {
    grid-template-columns: 1fr;
  }
}
</style>
