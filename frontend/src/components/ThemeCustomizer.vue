<script setup lang="ts">
import { computed } from 'vue'

import type { ThemeMode, ThemePreset } from '../theme'

const props = defineProps<{
  mode: ThemeMode
  accent: string
  presets: ThemePreset[]
}>()

const emit = defineEmits<{
  'update:mode': [value: ThemeMode]
  'update:accent': [value: string]
  reset: []
}>()

const accentPreview = computed(() => props.accent.toUpperCase())
const selectedPreset = computed(() =>
  props.presets.find((preset) => preset.accent.toLowerCase() === props.accent.toLowerCase())?.id,
)
</script>

<template>
  <section class="theme-card glass-panel">
    <div class="theme-header">
      <div>
        <span class="section-kicker">视觉系统</span>
        <h3>主题工作台</h3>
        <p>支持日间 / 夜间模式、自定义主题主色与预设配色。</p>
      </div>
      <button class="secondary-button" @click="emit('reset')">恢复默认</button>
    </div>

    <div class="theme-block">
      <span class="label">界面模式</span>
      <div class="segmented-control">
        <button
          :class="['segment', { active: mode === 'light' }]"
          @click="emit('update:mode', 'light')"
        >
          日间模式
        </button>
        <button
          :class="['segment', { active: mode === 'dark' }]"
          @click="emit('update:mode', 'dark')"
        >
          夜间模式
        </button>
      </div>
    </div>

    <div class="theme-block">
      <span class="label">主题预设</span>
      <div class="preset-grid">
        <button
          v-for="preset in presets"
          :key="preset.id"
          :class="['preset', { active: selectedPreset === preset.id }]"
          @click="emit('update:accent', preset.accent)"
        >
          <span class="swatch" :style="{ background: preset.accent }"></span>
          <span>{{ preset.label }}</span>
        </button>
      </div>
    </div>

    <div class="theme-block">
      <span class="label">自定义主色</span>
      <div class="accent-row">
        <input
          class="color-picker"
          :value="accent"
          type="color"
          @input="emit('update:accent', ($event.target as HTMLInputElement).value)"
        />
        <input
          class="hex-input"
          :value="accentPreview"
          @input="emit('update:accent', ($event.target as HTMLInputElement).value)"
        />
      </div>
    </div>

    <div class="preview-strip">
      <div class="preview-chip accent">Accent</div>
      <div class="preview-chip soft">Soft Surface</div>
      <div class="preview-chip line">Border</div>
    </div>

    <div class="mini-preview surface-box">
      <div class="mini-preview__top">
        <span class="mini-pill">{{ mode === 'dark' ? 'Night' : 'Light' }}</span>
        <span class="mini-pill soft">{{ accentPreview }}</span>
      </div>
      <div class="mini-preview__card"></div>
      <div class="mini-preview__line short"></div>
      <div class="mini-preview__line"></div>
      <div class="mini-preview__line faint"></div>
    </div>
  </section>
</template>

<style scoped>
.theme-card {
  display: grid;
  gap: 18px;
}

.theme-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
}

.theme-header h3 {
  margin: 6px 0 8px;
  font-size: 22px;
}

.theme-header p {
  margin: 0;
  color: var(--text-muted);
  line-height: 1.6;
}

.section-kicker {
  color: var(--accent);
  font-size: 12px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.theme-block {
  display: grid;
  gap: 10px;
}

.label {
  color: var(--text-muted);
  font-size: 13px;
}

.segmented-control {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.segment,
.preset,
.secondary-button {
  border: 1px solid var(--border-color);
  background: var(--surface-strong);
  color: var(--text-primary);
  border-radius: 18px;
  cursor: pointer;
  transition: 0.2s ease;
}

.segment {
  padding: 12px 14px;
}

.segment.active {
  background: rgba(var(--accent-rgb), 0.08);
  border-color: rgba(var(--accent-rgb), 0.2);
  color: var(--accent-strong);
}

.preset-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(110px, 1fr));
  gap: 10px;
}

.preset {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
}

.preset:hover,
.secondary-button:hover,
.segment:hover {
  transform: translateY(-1px);
  border-color: rgba(var(--accent-rgb), 0.32);
}

.preset.active {
  background: rgba(var(--accent-rgb), 0.08);
  border-color: rgba(var(--accent-rgb), 0.2);
  color: var(--accent-strong);
}

.swatch {
  width: 18px;
  height: 18px;
  border-radius: 999px;
  box-shadow: inset 0 0 0 2px rgba(255, 255, 255, 0.25);
}

.accent-row {
  display: grid;
  grid-template-columns: 68px 1fr;
  gap: 10px;
}

.color-picker,
.hex-input {
  border: 1px solid var(--border-color);
  background: var(--surface-muted);
  color: var(--text-primary);
  border-radius: 14px;
}

.color-picker {
  width: 100%;
  height: 48px;
  padding: 6px;
}

.hex-input {
  padding: 12px 14px;
}

.secondary-button {
  padding: 10px 14px;
}

.preview-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.preview-chip {
  padding: 10px 14px;
  border-radius: 999px;
  font-size: 13px;
}

.preview-chip.accent {
  background: var(--accent);
  color: var(--accent-contrast);
}

.preview-chip.soft {
  background: rgba(var(--accent-rgb), 0.12);
  color: var(--accent-strong);
}

.preview-chip.line {
  background: var(--surface-muted);
  border: 1px solid var(--border-color);
}

.surface-box {
  border: 1px solid var(--border-color);
  background: var(--surface-strong);
  border-radius: 24px;
  padding: 16px;
}

.mini-preview {
  display: grid;
  gap: 12px;
}

.mini-preview__top {
  display: flex;
  justify-content: space-between;
  gap: 8px;
}

.mini-pill {
  display: inline-flex;
  padding: 8px 12px;
  border-radius: 999px;
  background: var(--accent);
  color: var(--accent-contrast);
  font-size: 12px;
}

.mini-pill.soft {
  background: rgba(var(--accent-rgb), 0.12);
  color: var(--accent-strong);
}

.mini-preview__card {
  height: 72px;
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(var(--accent-rgb), 0.18), var(--surface-strong));
  border: 1px solid rgba(var(--accent-rgb), 0.2);
}

.mini-preview__line {
  height: 10px;
  border-radius: 999px;
  background: var(--surface-strong);
}

.mini-preview__line.short {
  width: 60%;
}

.mini-preview__line.faint {
  width: 75%;
  opacity: 0.6;
}

@media (max-width: 768px) {
  .theme-header {
    flex-direction: column;
  }
}
</style>
