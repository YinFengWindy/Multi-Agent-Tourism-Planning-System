<script setup lang="ts">
import type { LlmConfig } from '../types'

const props = defineProps<{
  config: LlmConfig
}>()

const emit = defineEmits<{
  update: [patch: Partial<LlmConfig>]
}>()

function updateField<K extends keyof LlmConfig>(key: K, value: LlmConfig[K]) {
  emit('update', { [key]: value })
}
</script>

<template>
  <section class="config-portal glass-panel">
    <div>
      <span class="eyebrow">Model Config</span>
      <h2>连接你的模型</h2>
      <p>参考图是平台型首页，所以这里把模型接入做成轻量配置抽屉。密钥仅保存在当前浏览器会话中。</p>
    </div>

    <div class="field-grid">
      <label>
        API Base URL
        <input :value="config.base_url" placeholder="https://api.openai.com/v1" @input="updateField('base_url', ($event.target as HTMLInputElement).value)" />
      </label>

      <label>
        API Key
        <input :value="config.api_key" type="password" placeholder="sk-..." @input="updateField('api_key', ($event.target as HTMLInputElement).value)" />
      </label>

      <label>
        Model
        <input :value="config.model" placeholder="gpt-4o-mini" @input="updateField('model', ($event.target as HTMLInputElement).value)" />
      </label>

      <label>
        Temperature
        <input :value="config.temperature" type="number" min="0" max="2" step="0.1" @input="updateField('temperature', Number(($event.target as HTMLInputElement).value || 0.3))" />
      </label>
    </div>

    <div class="surface-card security-note">
      <strong>安全说明</strong>
      <span>API Key 不持久化到后端数据库；默认只保存在当前浏览器会话。</span>
    </div>
  </section>
</template>

<style scoped>
.config-portal,
.field-grid {
  display: grid;
  gap: 18px;
}

.eyebrow {
  display: inline-flex;
  color: var(--accent);
  text-transform: uppercase;
  letter-spacing: 0.14em;
  font-size: 12px;
}

.config-portal h2,
.config-portal p,
.security-note span {
  margin: 0;
}

.config-portal p,
.security-note span {
  color: var(--text-secondary);
  line-height: 1.7;
}

.field-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

label {
  display: grid;
  gap: 8px;
  color: var(--text-secondary);
  font-size: 14px;
}

input {
  border: 1px solid var(--border-color);
  background: var(--surface-strong);
  color: var(--text-primary);
  border-radius: 16px;
  padding: 12px 14px;
}

.security-note {
  display: grid;
  gap: 6px;
}

@media (max-width: 720px) {
  .field-grid {
    grid-template-columns: 1fr;
  }
}
</style>
