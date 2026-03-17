<script setup lang="ts">
import ThemeCustomizer from '../components/ThemeCustomizer.vue'
import { useWorkspace } from '../composables/useWorkspace'
import { themePresets } from '../theme'

const {
  themeMode,
  accentColor,
  themeSummary,
  updateThemeMode,
  updateAccentColor,
  resetTheme,
} = useWorkspace()
</script>

<template>
  <section class="portal-page">
    <section class="glass-panel hero-panel">
      <div>
        <span class="eyebrow">Theme Portal</span>
        <h1>主题实验室</h1>
        <p>把主题设置也做成轻量门户页：预设、主色和预览组件保持与首页一致的留白和浅色层级。</p>
      </div>

      <div class="theme-badge">{{ themeSummary }}</div>
    </section>

    <section class="theme-grid">
      <ThemeCustomizer
        :mode="themeMode"
        :accent="accentColor"
        :presets="themePresets"
        @update:mode="updateThemeMode"
        @update:accent="updateAccentColor"
        @reset="resetTheme"
      />

      <section class="glass-panel preview-panel">
        <div>
          <span class="eyebrow">Live Preview</span>
          <h2>预览卡片</h2>
        </div>

        <div class="preview-grid">
          <article class="surface-card preview-card hero">
            <strong>Portal Hero</strong>
            <small>用于首页标题区、模式入口或活动横幅。</small>
          </article>

          <article class="surface-card preview-card stat">
            <span>Accent Token</span>
            <strong>{{ accentColor.toUpperCase() }}</strong>
          </article>

          <article class="surface-card preview-card pills">
            <span class="demo-pill primary">Primary</span>
            <span class="demo-pill soft">Soft</span>
            <span class="demo-pill line">Outline</span>
          </article>
        </div>
      </section>
    </section>
  </section>
</template>

<style scoped>
.portal-page,
.theme-grid,
.preview-grid,
.preview-panel {
  display: grid;
  gap: 18px;
}

.hero-panel {
  display: flex;
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
.preview-panel h2,
.preview-card strong,
.preview-card small,
.preview-card span {
  margin: 0;
}

.hero-panel h1 {
  margin-top: 6px;
  font-size: clamp(34px, 4vw, 48px);
}

.hero-panel p,
.preview-card small,
.preview-card span {
  color: var(--text-secondary);
  line-height: 1.8;
}

.theme-badge {
  display: inline-flex;
  align-items: center;
  padding: 10px 14px;
  border-radius: 999px;
  border: 1px solid rgba(var(--accent-rgb), 0.2);
  background: rgba(var(--accent-rgb), 0.08);
  color: var(--accent-strong);
}

.theme-grid {
  grid-template-columns: minmax(0, 1fr) 360px;
}

.preview-card {
  display: grid;
  gap: 10px;
}

.preview-card.hero {
  min-height: 180px;
  background: linear-gradient(135deg, rgba(var(--accent-rgb), 0.14), rgba(255, 255, 255, 0.96));
}

.preview-card strong {
  font-size: 20px;
}

.preview-card.pills {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.demo-pill {
  display: inline-flex;
  align-items: center;
  padding: 10px 14px;
  border-radius: 999px;
  font-size: 13px;
}

.demo-pill.primary {
  background: var(--accent);
  color: var(--accent-contrast);
}

.demo-pill.soft {
  background: rgba(var(--accent-rgb), 0.08);
  color: var(--accent-strong);
}

.demo-pill.line {
  border: 1px solid var(--border-color);
  background: var(--surface-muted);
}

@media (max-width: 1024px) {
  .hero-panel,
  .theme-grid {
    grid-template-columns: 1fr;
  }

  .hero-panel {
    flex-direction: column;
  }
}
</style>
