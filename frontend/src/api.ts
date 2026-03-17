import type {
  ChatPlanningRequest,
  ChatPlanningResponse,
  PlanEnvelope,
  PlanRequest,
  PortalHomeResponse,
  RecentPlansResponse,
  SystemHealthResponse,
} from './types'

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

async function readJsonOrThrow<T>(input: RequestInfo | URL, init: RequestInit, fallback: string): Promise<T> {
  const response = await fetch(input, init)
  if (!response.ok) {
    let message = fallback
    try {
      const payload = await response.json()
      if (payload && typeof payload === 'object') {
        message = String(payload.detail ?? payload.message ?? payload.error ?? fallback)
      }
    } catch {
      message = fallback
    }
    throw new Error(message)
  }
  return response.json()
}

export async function createPlan(payload: PlanRequest) {
  return readJsonOrThrow<{ plan_id: string; session_id: string; status: string; stream_url: string }>(
    `${API_BASE}/api/v1/plans`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    },
    '创建规划失败',
  )
}

export async function fetchPlan(planId: string): Promise<PlanEnvelope> {
  return readJsonOrThrow<PlanEnvelope>(`${API_BASE}/api/v1/plans/${planId}`, { cache: 'no-store' }, '获取规划失败')
}

export async function replanPlan(planId: string, updatedConstraints: Record<string, unknown>) {
  return readJsonOrThrow<{ plan_id: string; status: string; version: number; stream_url: string }>(
    `${API_BASE}/api/v1/plans/${planId}/replan`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reason: 'user_replan', updated_constraints: updatedConstraints }),
    },
    '重规划失败',
  )
}

export function buildPlanStreamUrl(planId: string) {
  return `${API_BASE}/api/v1/plans/${planId}/stream`
}

export async function fetchRecentPlans(limit = 8) {
  return readJsonOrThrow<RecentPlansResponse>(
    `${API_BASE}/api/v1/plans/recent?limit=${limit}`,
    { cache: 'no-store' },
    '获取最近规划失败',
  )
}

export async function fetchSystemHealth() {
  return readJsonOrThrow<SystemHealthResponse>(
    `${API_BASE}/api/v1/system/health`,
    { cache: 'no-store' },
    '获取系统状态失败',
  )
}

export async function sendChatPlanning(payload: ChatPlanningRequest) {
  return readJsonOrThrow<ChatPlanningResponse>(
    `${API_BASE}/api/v1/chat/plans`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    },
    '对话规划失败',
  )
}

export async function fetchPortalHome() {
  return readJsonOrThrow<PortalHomeResponse>(
    `${API_BASE}/api/v1/portal/home`,
    { cache: 'no-store' },
    '获取首页门户数据失败',
  )
}
