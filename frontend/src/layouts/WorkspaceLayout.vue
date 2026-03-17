<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { RouterLink, RouterView, useRoute } from 'vue-router'

import BrandLogo from '../components/BrandLogo.vue'
import { useWorkspace } from '../composables/useWorkspace'

const {
  currentStatus,
  themeSummary,
  initializeWorkspace,
} = useWorkspace()

const route = useRoute()

const sidebarItems = [
  { name: 'overview', label: '灵感', icon: 'home' },
  { name: 'execution', label: '生成', icon: 'spark' },
  { name: 'results', label: '资产', icon: 'folder' },
  { name: 'theme', label: '画布', icon: 'grid' },
]

const activeRouteName = computed(() => String(route.name ?? 'overview'))

const iconPaths: Record<string, string[]> = {
  home: [
    'M4.5 12.1L11.2 5.86C11.65 5.44 12.35 5.44 12.8 5.86L19.5 12.1',
    'M6.75 10.8V18.2C6.75 18.64 7.11 19 7.55 19H10.2V15.05C10.2 14.5 10.65 14.05 11.2 14.05H12.8C13.35 14.05 13.8 14.5 13.8 15.05V19H16.45C16.89 19 17.25 18.64 17.25 18.2V10.8',
  ],
  spark: [
    'M12 4.2L13.65 8.35L17.8 10L13.65 11.65L12 15.8L10.35 11.65L6.2 10L10.35 8.35L12 4.2Z',
    'M6 15.8L6.68 17.32L8.2 18L6.68 18.68L6 20.2L5.32 18.68L3.8 18L5.32 17.32L6 15.8Z',
  ],
  folder: [
    'M4.5 8.2C4.5 7.54 5.04 7 5.7 7H8.55C8.87 7 9.18 7.13 9.4 7.35L10.4 8.35C10.62 8.57 10.93 8.7 11.25 8.7H18.3C18.96 8.7 19.5 9.24 19.5 9.9V16.3C19.5 16.96 18.96 17.5 18.3 17.5H5.7C5.04 17.5 4.5 16.96 4.5 16.3V8.2Z',
  ],
  grid: [
    'M5 5H9V9H5V5Z',
    'M15 5H19V9H15V5Z',
    'M5 15H9V19H5V15Z',
    'M15 15H19V19H15V15Z',
  ],
}

onMounted(() => {
  initializeWorkspace()
})
</script>

<template>
  <main class="workspace-shell">
    <aside class="portal-sidebar">
      <div class="portal-sidebar__brand">
        <BrandLogo :size="36" />
      </div>

      <nav class="portal-sidebar__menu">
        <RouterLink
          v-for="item in sidebarItems"
          :key="item.name"
          :to="{ name: item.name }"
          :class="['portal-nav-link', { active: activeRouteName === item.name }]"
        >
          <span class="portal-nav-link__icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none">
              <path
                v-for="(path, index) in iconPaths[item.icon]"
                :key="`${item.name}-${index}`"
                :d="path"
                stroke="currentColor"
                stroke-width="1.8"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>
          </span>
          <span>{{ item.label }}</span>
        </RouterLink>
      </nav>
    </aside>

    <section class="workspace-content">
      <header class="workspace-topbar glass-panel">
        <div class="workspace-topbar__brand">
          <BrandLogo :size="34" />
          <div>
            <strong>AI Tourism Workspace</strong>
            <small>Agent-first travel creation platform</small>
          </div>
        </div>

        <div class="workspace-topbar__meta">
          <span class="meta-pill">{{ themeSummary }}</span>
          <span class="meta-pill">{{ currentStatus }}</span>
          <span class="meta-pill">目标目录：Multi-Agent Tourism Planning System</span>
        </div>
      </header>

      <RouterView />
    </section>
  </main>
</template>

<style scoped>
.workspace-shell {
  display: grid;
  grid-template-columns: 76px minmax(0, 1fr);
  gap: 20px;
  min-height: 100vh;
  padding: 16px;
}

.portal-sidebar,
.workspace-content,
.workspace-topbar,
.workspace-topbar__brand,
.workspace-topbar__meta {
  display: grid;
}

.portal-sidebar {
  align-content: start;
  gap: 28px;
  padding: 18px 14px;
  background: var(--sidebar-bg);
  border: 1px solid var(--sidebar-border);
  border-radius: 28px;
  box-shadow: 0 18px 40px rgba(var(--sidebar-shadow), 0.08);
  position: sticky;
  top: 16px;
  height: calc(100vh - 32px);
}

.portal-sidebar__brand {
  justify-items: center;
}

.portal-sidebar__menu {
  display: grid;
  gap: 10px;
}

.portal-nav-link {
  display: grid;
  justify-items: center;
  gap: 8px;
  padding: 12px 8px;
  border-radius: 18px;
  text-decoration: none;
  color: var(--sidebar-muted);
  font-size: 12px;
  border: 1px solid transparent;
}

.portal-nav-link.active {
  color: var(--sidebar-text);
  background: var(--sidebar-active-bg);
  border-color: var(--sidebar-active-border);
}

.portal-nav-link__icon {
  width: 38px;
  height: 38px;
  display: grid;
  place-items: center;
  border-radius: 14px;
}

.portal-nav-link.active .portal-nav-link__icon {
  background: var(--sidebar-icon-active-bg);
}

.portal-nav-link__icon svg {
  width: 22px;
  height: 22px;
}

.workspace-content {
  align-content: start;
  gap: 18px;
}

.workspace-topbar {
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 18px;
  align-items: center;
  padding-block: 18px;
}

.workspace-topbar__brand {
  grid-auto-flow: column;
  justify-content: start;
  align-items: center;
  gap: 12px;
}

.workspace-topbar__brand strong {
  display: block;
}

.workspace-topbar__brand small,
.meta-pill {
  color: var(--text-secondary);
}

.workspace-topbar__meta {
  grid-auto-flow: column;
  gap: 10px;
  justify-content: end;
}

.meta-pill {
  display: inline-flex;
  align-items: center;
  padding: 10px 14px;
  border-radius: 999px;
  background: var(--surface);
  border: 1px solid var(--border-color);
  font-size: 12px;
}

@media (max-width: 1024px) {
  .workspace-shell {
    grid-template-columns: 1fr;
  }

  .portal-sidebar {
    position: static;
    height: auto;
    grid-template-columns: 1fr;
  }

  .portal-sidebar__menu {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }

  .workspace-topbar {
    grid-template-columns: 1fr;
  }

  .workspace-topbar__meta {
    grid-auto-flow: row;
    justify-content: start;
  }
}

@media (max-width: 640px) {
  .portal-sidebar__menu {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
