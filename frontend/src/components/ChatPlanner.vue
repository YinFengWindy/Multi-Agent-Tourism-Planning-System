<script setup lang="ts">
import { ref } from 'vue'

import type { ChatMessage } from '../types'

const props = defineProps<{
  messages: ChatMessage[]
  loading: boolean
  error: string
  starterPrompts: string[]
  placeholder: string
}>()

const emit = defineEmits<{
  send: [content: string]
  reset: []
}>()

const draft = ref('')

function submit() {
  const content = draft.value.trim()
  if (!content || props.loading) {
    return
  }
  emit('send', content)
  draft.value = ''
}
</script>

<template>
  <section class="chat-portal glass-panel">
    <div class="chat-composer surface-card">
      <div class="chat-composer__input">
        <button class="upload-tile" type="button">+</button>
        <textarea v-model="draft" :placeholder="placeholder"></textarea>
      </div>

      <div class="chat-composer__footer">
        <div class="mode-row">
          <span class="mode-chip mode-chip--accent">Agent 模式</span>
          <span class="mode-chip">旅游创作</span>
          <span class="mode-chip">自动</span>
          <span class="mode-chip">灵感搜索</span>
          <span class="mode-chip">创意设计</span>
        </div>

        <button class="send-circle" type="button" :disabled="loading" @click="submit">
          {{ loading ? '…' : '↑' }}
        </button>
      </div>
    </div>

    <div class="prompt-row">
      <button v-for="prompt in starterPrompts" :key="prompt" class="prompt-chip" type="button" @click="emit('send', prompt)">
        {{ prompt }}
      </button>
      <button class="prompt-chip ghost-chip" type="button" @click="emit('reset')">清空会话</button>
    </div>

    <div class="message-list">
      <article v-for="(message, index) in messages" :key="`${message.role}-${index}`" :class="['message-item', message.role]">
        <div class="message-bubble">{{ message.content }}</div>
      </article>
    </div>

    <div v-if="error" class="error-banner surface-card">{{ error }}</div>
  </section>
</template>

<style scoped>
.chat-portal,
.chat-composer,
.chat-composer__input,
.chat-composer__footer,
.prompt-row,
.mode-row,
.message-list {
  display: grid;
  gap: 14px;
}

.chat-composer {
  padding: 18px;
  gap: 18px;
}

.chat-composer__input {
  grid-template-columns: 60px minmax(0, 1fr);
  align-items: start;
}

.upload-tile {
  width: 52px;
  height: 72px;
  border: 1px dashed var(--border-color);
  background: linear-gradient(180deg, #f6f7fa, #eff2f7);
  color: var(--text-muted);
  border-radius: 16px;
  font-size: 28px;
}

textarea {
  min-height: 132px;
  resize: vertical;
  border: none;
  background: transparent;
  color: var(--text-primary);
  padding: 8px 0;
  font-size: 18px;
  line-height: 1.8;
}

.chat-composer__footer {
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
}

.mode-row,
.prompt-row {
  grid-auto-flow: column;
  grid-auto-columns: max-content;
  overflow: auto;
}

.mode-chip,
.prompt-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 10px 14px;
  border-radius: 14px;
  border: 1px solid var(--border-color);
  background: #ffffff;
  color: var(--text-secondary);
  white-space: nowrap;
}

.mode-chip--accent,
.prompt-chip {
  background: rgba(var(--accent-rgb), 0.08);
  color: var(--accent-strong);
  border-color: rgba(var(--accent-rgb), 0.18);
}

.ghost-chip {
  background: var(--surface);
  color: var(--text-secondary);
}

.send-circle {
  width: 44px;
  height: 44px;
  border-radius: 999px;
  border: none;
  background: linear-gradient(135deg, var(--accent), var(--accent-strong));
  color: var(--accent-contrast);
  font-size: 20px;
}

.message-list {
  max-height: 420px;
  overflow: auto;
}

.message-item {
  display: grid;
}

.message-item.user {
  justify-items: end;
}

.message-bubble {
  max-width: min(100%, 840px);
  padding: 16px 18px;
  border-radius: 20px;
  background: #ffffff;
  border: 1px solid var(--border-color);
  line-height: 1.8;
  white-space: pre-wrap;
}

.message-item.user .message-bubble {
  background: linear-gradient(135deg, var(--accent), var(--accent-strong));
  color: var(--accent-contrast);
  border-color: transparent;
}

.error-banner {
  color: var(--danger);
}

@media (max-width: 720px) {
  .chat-composer__input,
  .chat-composer__footer {
    grid-template-columns: 1fr;
  }
}
</style>
