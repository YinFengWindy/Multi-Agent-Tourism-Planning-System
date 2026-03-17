<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import ChatPlanner from '../components/ChatPlanner.vue'
import ModelConfigPanel from '../components/ModelConfigPanel.vue'
import { fetchPortalHome } from '../api'
import { useChatPlanner } from '../composables/useChatPlanner'
import { useWorkspace } from '../composables/useWorkspace'
import type { PortalGalleryCard, PortalHomeResponse } from '../types'

const defaultPortalHome: PortalHomeResponse = {
  headline: '开启你的 Agent 模式，立即造梦',
  subheadline: '用对话、结果与资产流一体化的方式组织旅行灵感、规划方案与最终交付。',
  prompt_placeholder: '告诉我你的出发地、目的地、日期、预算、人数，或继续修改已有方案……',
  hero_chips: ['用户自配模型', '聊天主入口', '结果联动', '资产沉淀'],
  mode_cards: [
    { title: '旅行灵感', subtitle: '从一句话需求开始', badge: 'Chat', accent: 'azure' },
    { title: 'Agent 模式', subtitle: '自动拆解约束与计划', badge: 'Agent', accent: 'cyan' },
    { title: '结果生成', subtitle: '预算、路线与风险联动', badge: 'Result', accent: 'violet' },
    { title: '资产沉淀', subtitle: '最近规划与结果复用', badge: 'Asset', accent: 'rose' },
  ],
  gallery_cards: [
    { title: '周末城市微度假', subtitle: '高铁两小时圈 · 轻节奏美食路线', badge: '发现', size: 'wide', theme: 'azure' },
    { title: '粉色春日草坡', subtitle: '适合情侣与摄影主题行程', badge: '灵感', size: 'medium', theme: 'mint' },
    { title: '云上小屋', subtitle: '适合节气感与治愈系目的地', badge: '路线', size: 'medium', theme: 'gold' },
    { title: '萌宠亲子农场', subtitle: '适合家庭互动与低龄陪伴', badge: '亲子', size: 'tall', theme: 'peach' },
    { title: '夜色下的创作驻留', subtitle: '适合内容创作者与城市漫游', badge: '专题', size: 'medium', theme: 'slate' },
    { title: '晨雾庭院早餐', subtitle: '适合慢节奏酒店度假灵感', badge: '住宿', size: 'medium', theme: 'sage' },
  ],
}

const {
  chatMessages,
  chatLoading,
  chatError,
  llmConfig,
  starterPrompts,
  initializeChatPlanner,
  updateLlmConfig,
  resetConversation,
  sendUserMessage,
} = useChatPlanner()

const {
  serviceHealth,
  healthLoading,
  healthSummary,
  recentPlans,
  handleResumePlan,
  refreshRecentPlans,
  refreshServiceHealth,
  initializeWorkspace,
} = useWorkspace()

const portalHome = ref<PortalHomeResponse>(defaultPortalHome)
const search = ref('')
const activeTab = ref<'发现' | '短片' | '活动'>('发现')
const showConfig = ref(false)
const galleryTabs = ['发现', '短片', '活动'] as const

initializeWorkspace()
initializeChatPlanner()

onMounted(async () => {
  try {
    portalHome.value = await fetchPortalHome()
  } catch {
    portalHome.value = defaultPortalHome
  }
  void refreshServiceHealth()
  void refreshRecentPlans()
})

function setTab(tab: string) {
  if (tab === '发现' || tab === '短片' || tab === '活动') {
    activeTab.value = tab
  }
}

const filteredGallery = computed(() => {
  const cards = portalHome.value.gallery_cards ?? []
  return cards.filter((card) => {
    const tabMatch = activeTab.value === '发现'
      ? true
      : activeTab.value === '短片'
        ? card.size !== 'wide'
        : ['专题', '亲子', '住宿'].includes(card.badge)
    const searchMatch = !search.value.trim()
      || `${card.title}${card.subtitle}${card.badge}`.includes(search.value.trim())
    return tabMatch && searchMatch
  })
})

function formatTime(value: string) {
  return new Date(value).toLocaleString('zh-CN', { hour12: false })
}

function statusLabel(status: string) {
  const dictionary: Record<string, string> = {
    ok: '正常',
    degraded: '降级',
    down: '不可用',
    planning: '规划中',
    completed: '已完成',
    failed: '失败',
    unknown: '未知',
  }
  return dictionary[status] ?? status
}

function galleryClass(card: PortalGalleryCard) {
  return [`gallery-card`, `gallery-card--${card.size}`, `gallery-card--${card.theme}`]
}
</script>

<template>
  <section class="portal-home">
    <section class="hero-panel glass-panel">
      <div class="hero-panel__copy">
        <span class="eyebrow">AI Creation Portal</span>
        <h1>{{ portalHome.headline }}</h1>
        <p>{{ portalHome.subheadline }}</p>
      </div>

      <div class="hero-actions">
        <button class="hero-chip hero-chip--accent" type="button" @click="showConfig = !showConfig">
          {{ showConfig ? '收起模型配置' : '用户自配模型' }}
        </button>
        <span v-for="chip in portalHome.hero_chips" :key="chip" class="hero-chip">{{ chip }}</span>
      </div>
    </section>

    <ModelConfigPanel v-if="showConfig" :config="llmConfig" @update="updateLlmConfig" />

    <ChatPlanner
      :messages="chatMessages"
      :loading="chatLoading"
      :error="chatError"
      :starter-prompts="starterPrompts"
      :placeholder="portalHome.prompt_placeholder"
      @send="sendUserMessage"
      @reset="resetConversation"
    />

    <section class="mode-strip">
      <article v-for="card in portalHome.mode_cards" :key="card.title" class="surface-card mode-card">
        <div class="mode-card__badge">{{ card.badge }}</div>
        <strong>{{ card.title }}</strong>
        <span>{{ card.subtitle }}</span>
      </article>
    </section>

    <section class="portal-grid">
      <section class="gallery-panel glass-panel">
        <div class="gallery-toolbar">
          <div class="gallery-tabs">
            <button v-for="tab in galleryTabs" :key="tab" :class="['gallery-tab', { active: activeTab === tab }]" type="button" @click="setTab(tab)">
              {{ tab }}
            </button>
          </div>

          <input v-model="search" class="gallery-search" placeholder="搜索灵感词或主题" />
        </div>

        <div class="gallery-waterfall">
          <article v-for="card in filteredGallery" :key="`${card.title}-${card.badge}`" :class="galleryClass(card)">
            <span class="gallery-card__badge">{{ card.badge }}</span>
            <div class="gallery-card__body">
              <strong>{{ card.title }}</strong>
              <p>{{ card.subtitle }}</p>
            </div>
          </article>
        </div>
      </section>

      <aside class="portal-side">
        <section class="glass-panel service-panel">
          <div class="panel-header">
            <div>
              <span class="eyebrow">System Health</span>
              <h2>服务状态</h2>
            </div>
            <button class="link-chip" type="button" @click="refreshServiceHealth">
              {{ healthLoading ? '检查中...' : '刷新状态' }}
            </button>
          </div>

          <div class="service-summary">
            <strong>{{ statusLabel(healthSummary.overall) }}</strong>
            <span>健康服务 {{ healthSummary.healthyCount }} / {{ healthSummary.total }}</span>
          </div>

          <div class="service-list">
            <article v-for="service in serviceHealth?.services ?? []" :key="service.service" class="surface-card service-card">
              <div class="service-card__top">
                <strong>{{ service.service }}</strong>
                <span :class="['status-pill', service.status]">{{ statusLabel(service.status) }}</span>
              </div>
              <small>{{ service.detail ?? '状态已同步' }}</small>
            </article>
          </div>
        </section>

        <section class="glass-panel recent-panel">
          <div class="panel-header">
            <div>
              <span class="eyebrow">Recent Sessions</span>
              <h2>最近规划</h2>
            </div>
            <span class="link-chip muted-chip">{{ recentPlans.length }} 条</span>
          </div>

          <div class="recent-list">
            <article v-for="plan in recentPlans.slice(0, 4)" :key="plan.plan_id" class="surface-card recent-card">
              <div class="recent-card__top">
                <strong>{{ plan.origin_city }} → {{ plan.destination_cities.join(' / ') }}</strong>
                <span :class="['status-pill', plan.status]">{{ statusLabel(plan.status) }}</span>
              </div>
              <small>{{ formatTime(plan.updated_at) }}</small>
              <p>{{ plan.summary ?? '等待生成规划摘要...' }}</p>
              <button class="resume-button" type="button" @click="handleResumePlan(plan.plan_id)">恢复查看</button>
            </article>
          </div>
        </section>
      </aside>
    </section>
  </section>
</template>

<style scoped>
.portal-home,
.portal-grid,
.portal-side,
.service-list,
.recent-list {
  display: grid;
  gap: 18px;
}

.hero-panel,
.hero-panel__copy,
.hero-actions,
.gallery-toolbar,
.gallery-tabs,
.panel-header,
.service-card__top,
.recent-card__top,
.service-summary {
  display: flex;
}

.hero-panel {
  align-items: center;
  flex-direction: column;
  justify-content: center;
  min-height: 210px;
  gap: 22px;
  text-align: center;
}

.hero-panel__copy {
  flex-direction: column;
  gap: 12px;
  align-items: center;
}

.eyebrow {
  display: inline-flex;
  color: var(--accent);
  text-transform: uppercase;
  letter-spacing: 0.14em;
  font-size: 12px;
}

.hero-panel h1,
.panel-header h2,
.gallery-card__body p,
.recent-card p,
.hero-panel__copy p {
  margin: 0;
}

.hero-panel h1 {
  font-size: clamp(36px, 4vw, 52px);
}

.hero-panel__copy p,
.gallery-card__body p,
.recent-card p,
.service-card small {
  color: var(--text-secondary);
  line-height: 1.8;
}

.hero-actions {
  flex-wrap: wrap;
  justify-content: center;
  gap: 10px;
}

.hero-chip,
.link-chip,
.status-pill,
.mode-card__badge,
.gallery-card__badge,
.resume-button,
.gallery-tab {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  font-size: 12px;
}

.hero-chip,
.link-chip,
.gallery-tab,
.muted-chip {
  padding: 10px 14px;
  border: 1px solid var(--border-color);
  background: var(--surface);
  color: var(--text-secondary);
}

.hero-chip--accent,
.gallery-tab.active {
  color: var(--accent-strong);
  border-color: rgba(var(--accent-rgb), 0.18);
  background: rgba(var(--accent-rgb), 0.08);
}

.mode-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
}

.mode-card {
  display: grid;
  gap: 8px;
}

.mode-card__badge {
  width: fit-content;
  padding: 8px 10px;
  background: rgba(var(--accent-rgb), 0.08);
  color: var(--accent-strong);
}

.mode-card strong {
  font-size: 18px;
}

.mode-card span {
  color: var(--text-secondary);
}

.portal-grid {
  grid-template-columns: minmax(0, 1.2fr) 360px;
}

.gallery-toolbar {
  justify-content: space-between;
  gap: 16px;
  align-items: center;
}

.gallery-tabs {
  gap: 10px;
}

.gallery-search {
  border: 1px solid var(--border-color);
  background: var(--surface);
  color: var(--text-primary);
  border-radius: 16px;
  padding: 12px 16px;
  min-width: 260px;
}

.gallery-waterfall {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.gallery-card {
  position: relative;
  overflow: hidden;
  min-height: 240px;
  padding: 18px;
  border-radius: 28px;
  display: grid;
  align-content: end;
  border: 1px solid rgba(255, 255, 255, 0.45);
  box-shadow: 0 18px 40px rgba(var(--shadow-color), 0.08);
}

.gallery-card::before {
  content: '';
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at 75% 25%, rgba(255, 255, 255, 0.7), transparent 24%),
    radial-gradient(circle at 30% 72%, rgba(255, 255, 255, 0.45), transparent 28%);
  opacity: 0.9;
}

.gallery-card__badge,
.gallery-card__body {
  position: relative;
  z-index: 1;
}

.gallery-card__badge {
  width: fit-content;
  padding: 8px 10px;
  margin-bottom: auto;
  background: rgba(255, 255, 255, 0.74);
  color: #263244;
}

.gallery-card__body {
  display: grid;
  gap: 8px;
}

.gallery-card__body strong {
  font-size: 26px;
  color: #111827;
}

.gallery-card--wide {
  grid-column: span 2;
  min-height: 300px;
}

.gallery-card--tall {
  min-height: 360px;
}

.gallery-card--azure { background: linear-gradient(135deg, #7fb5ff, #d8ebff); }
.gallery-card--mint { background: linear-gradient(135deg, #b7ecce, #effff4); }
.gallery-card--gold { background: linear-gradient(135deg, #ffeaa2, #fff6d8); }
.gallery-card--peach { background: linear-gradient(135deg, #ffd7c7, #fff1eb); }
.gallery-card--slate { background: linear-gradient(135deg, #cad4e6, #eff3fa); }
.gallery-card--sage { background: linear-gradient(135deg, #d6ebcf, #f7fff2); }

.panel-header,
.service-card__top,
.recent-card__top,
.service-summary {
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}

.service-summary {
  padding: 16px 18px;
  border-radius: 22px;
  background: var(--surface);
  border: 1px solid var(--border-color);
}

.service-summary strong {
  font-size: 22px;
}

.status-pill {
  padding: 8px 10px;
  border: 1px solid var(--border-color);
}

.status-pill.ok,
.status-pill.completed {
  background: rgba(var(--success-rgb), 0.12);
  color: var(--success);
}

.status-pill.degraded,
.status-pill.planning {
  background: rgba(var(--warning-rgb), 0.12);
  color: var(--warning);
}

.status-pill.down,
.status-pill.failed {
  background: rgba(var(--danger-rgb), 0.12);
  color: var(--danger);
}

.service-card,
.recent-card {
  display: grid;
  gap: 10px;
}

.resume-button {
  width: fit-content;
  padding: 10px 14px;
  border: none;
  cursor: pointer;
  background: linear-gradient(135deg, var(--accent), var(--accent-strong));
  color: var(--accent-contrast);
}

@media (max-width: 1200px) {
  .portal-grid,
  .mode-strip,
  .gallery-waterfall {
    grid-template-columns: 1fr;
  }

  .gallery-card--wide {
    grid-column: span 1;
  }
}

@media (max-width: 720px) {
  .gallery-toolbar,
  .panel-header,
  .service-card__top,
  .recent-card__top,
  .service-summary {
    flex-direction: column;
    align-items: flex-start;
  }

  .gallery-search {
    min-width: 0;
    width: 100%;
  }
}
</style>
