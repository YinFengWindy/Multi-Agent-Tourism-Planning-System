import { computed, ref } from 'vue'

import { sendChatPlanning } from '../api'
import type { ChatMessage, LlmConfig } from '../types'
import { useWorkspace } from './useWorkspace'

const STORAGE_KEYS = {
  messages: 'mtp-chat-messages',
  llmConfig: 'mtp-llm-config',
}

const chatMessages = ref<ChatMessage[]>([])
const chatLoading = ref(false)
const chatError = ref('')
const llmConfig = ref<LlmConfig>({
  base_url: 'https://api.openai.com/v1',
  api_key: '',
  model: 'gpt-4o-mini',
  temperature: 0.3,
})

let initialized = false

const starterPrompts = [
  '我想五一从上海去杭州和乌镇玩 3 天，预算 4000 左右。',
  '帮我规划一个北京周末城市文化游，两个人，想看博物馆和地标。',
  '把当前方案改得更省预算一些，但不要太早出门。',
]

const canChat = computed(() => Boolean(llmConfig.value.api_key.trim() && llmConfig.value.model.trim() && llmConfig.value.base_url.trim()))

function persistSession() {
  if (typeof window === 'undefined') {
    return
  }
  window.sessionStorage.setItem(STORAGE_KEYS.messages, JSON.stringify(chatMessages.value))
  window.sessionStorage.setItem(STORAGE_KEYS.llmConfig, JSON.stringify(llmConfig.value))
}

function initializeChatPlanner() {
  if (initialized || typeof window === 'undefined') {
    return
  }

  const storedMessages = window.sessionStorage.getItem(STORAGE_KEYS.messages)
  const storedConfig = window.sessionStorage.getItem(STORAGE_KEYS.llmConfig)

  if (storedMessages) {
    try {
      chatMessages.value = JSON.parse(storedMessages) as ChatMessage[]
    } catch {
      chatMessages.value = []
    }
  }

  if (storedConfig) {
    try {
      llmConfig.value = {
        ...llmConfig.value,
        ...(JSON.parse(storedConfig) as Partial<LlmConfig>),
      }
    } catch {
      llmConfig.value = llmConfig.value
    }
  }

  if (!chatMessages.value.length) {
    chatMessages.value = [
      {
        role: 'assistant',
        content: '你好，我是你的旅游规划助手。先在右侧填入模型配置，再直接用自然语言告诉我你的出发地、目的地、日期、人数和预算。',
      },
    ]
  }

  persistSession()
  initialized = true
}

function updateLlmConfig(patch: Partial<LlmConfig>) {
  llmConfig.value = {
    ...llmConfig.value,
    ...patch,
  }
  persistSession()
}

function resetConversation() {
  chatMessages.value = [
    {
      role: 'assistant',
      content: '会话已清空。你可以重新告诉我新的旅游需求，或继续修改现有方案。',
    },
  ]
  chatError.value = ''
  persistSession()
}

async function sendUserMessage(content: string) {
  const trimmed = content.trim()
  if (!trimmed) {
    return
  }
  if (!canChat.value) {
    chatError.value = '请先填写 API Base URL、API Key 和模型名称。'
    return
  }

  const workspace = useWorkspace()

  chatError.value = ''
  chatLoading.value = true
  chatMessages.value = [...chatMessages.value, { role: 'user', content: trimmed }]
  persistSession()

  try {
    const response = await sendChatPlanning({
      messages: chatMessages.value,
      llm_config: llmConfig.value,
      current_plan_id: workspace.currentPlanId.value || undefined,
      current_request: workspace.lastPayload.value ?? undefined,
    })

    chatMessages.value = [...chatMessages.value, { role: 'assistant', content: response.assistant_message }]
    persistSession()

    if (response.plan_id) {
      await workspace.handleResumePlan(response.plan_id)
    }
  } catch (reason) {
    chatError.value = reason instanceof Error ? reason.message : '对话规划失败'
  } finally {
    chatLoading.value = false
  }
}

export function useChatPlanner() {
  return {
    chatMessages,
    chatLoading,
    chatError,
    llmConfig,
    canChat,
    starterPrompts,
    initializeChatPlanner,
    updateLlmConfig,
    resetConversation,
    sendUserMessage,
  }
}
