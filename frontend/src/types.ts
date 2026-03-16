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
