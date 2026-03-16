import type { PlanEnvelope, PlanRequest } from './types'

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export async function createPlan(payload: PlanRequest) {
  const response = await fetch(`${API_BASE}/api/v1/plans`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) {
    throw new Error('创建规划失败')
  }
  return response.json()
}

export async function fetchPlan(planId: string): Promise<PlanEnvelope> {
  const response = await fetch(`${API_BASE}/api/v1/plans/${planId}`)
  if (!response.ok) {
    throw new Error('获取规划失败')
  }
  return response.json()
}

export async function replanPlan(planId: string, updatedConstraints: Record<string, unknown>) {
  const response = await fetch(`${API_BASE}/api/v1/plans/${planId}/replan`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ reason: 'user_replan', updated_constraints: updatedConstraints }),
  })
  if (!response.ok) {
    throw new Error('重规划失败')
  }
  return response.json()
}

export function buildPlanStreamUrl(planId: string) {
  return `${API_BASE}/api/v1/plans/${planId}/stream`
}

