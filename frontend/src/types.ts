export interface TravelConstraints {
  transport_mode: string[]
  hotel_level: string
  daily_start_after: string
  daily_end_before: string
  budget_mode: string
}

export interface PlanRequest {
  origin_city: string
  destination_cities: string[]
  start_date: string
  end_date: string
  travelers: number
  budget: number
  preferences: string[]
  constraints: TravelConstraints
}

export interface PlanEvent {
  type: string
  message: string
  data: Record<string, unknown>
  timestamp: string
}

export interface DayItem {
  time: string
  title: string
  description: string
}

export interface DayPlan {
  day_index: number
  date: string
  city: string
  theme: string
  items: DayItem[]
  hotel_tip?: string
  transport_tip?: string
}

export interface PlanResult {
  plan_id: string
  status: string
  summary: string
  days: DayPlan[]
  warnings: string[]
  fallback_plans: string[]
  transport_options: Array<Record<string, unknown>>
  hotel_options: Array<Record<string, unknown>>
  budget_breakdown: Record<string, number>
  domain_insights?: Record<
    string,
    {
      agent_type: string
      summary: string
      highlights: string[]
      warnings: string[]
      confidence_score: number
      structured_data?: Record<string, unknown>
      tool_summaries?: string[]
    }
  >
}

export interface PlanEnvelope {
  plan_id: string
  status: string
  request: PlanRequest
  events: PlanEvent[]
  result?: PlanResult
  error?: string
  version: number
}

export interface PlanSummary {
  plan_id: string
  status: string
  version: number
  origin_city: string
  destination_cities: string[]
  travelers: number
  budget: number
  summary?: string
  warning_count: number
  day_count: number
  created_at: string
  updated_at: string
}

export interface RecentPlansResponse {
  items: PlanSummary[]
}

export interface ServiceHealth {
  service: string
  status: string
  url?: string | null
  latency_ms?: number | null
  detail?: string | null
}

export interface SystemHealthResponse {
  status: string
  generated_at: string
  services: ServiceHealth[]
}

export interface ChatMessage {
  role: 'system' | 'assistant' | 'user'
  content: string
}

export interface LlmConfig {
  base_url: string
  api_key: string
  model: string
  temperature: number
}

export interface ChatPlanningRequest {
  messages: ChatMessage[]
  llm_config: LlmConfig
  current_plan_id?: string
  current_request?: PlanRequest
}

export interface ChatPlanningResponse {
  assistant_message: string
  action: 'ask' | 'create_plan' | 'replan'
  status: string
  plan_id?: string
  stream_url?: string
  request_preview?: PlanRequest
}

export interface PortalModeCard {
  title: string
  subtitle: string
  badge: string
  accent: string
}

export interface PortalGalleryCard {
  title: string
  subtitle: string
  badge: string
  size: 'wide' | 'medium' | 'tall'
  theme: string
}

export interface PortalHomeResponse {
  headline: string
  subheadline: string
  prompt_placeholder: string
  hero_chips: string[]
  mode_cards: PortalModeCard[]
  gallery_cards: PortalGalleryCard[]
}
