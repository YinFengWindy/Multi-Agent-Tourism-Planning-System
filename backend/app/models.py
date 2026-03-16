from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class TravelConstraints(BaseModel):
    transport_mode: list[str] = Field(default_factory=lambda: ["高铁", "地铁", "打车"])
    hotel_level: str = "舒适型"
    daily_start_after: str = "09:00"
    daily_end_before: str = "21:30"
    budget_mode: str = "balanced"


class PlanRequest(BaseModel):
    origin_city: str
    destination_cities: list[str]
    start_date: str
    end_date: str
    travelers: int = 1
    budget: float = 3000
    preferences: list[str] = Field(default_factory=list)
    constraints: TravelConstraints = Field(default_factory=TravelConstraints)


class PlanEvent(BaseModel):
    type: str
    message: str
    data: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ToolExecutionRequest(BaseModel):
    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    trace_id: str | None = None


class ToolExecutionResponse(BaseModel):
    success: bool = True
    source: str = "mock-provider"
    latency_ms: int = 0
    cached: bool = False
    data: dict[str, Any] = Field(default_factory=dict)
    normalized_summary: str = ""


class DomainInsight(BaseModel):
    agent_type: str
    summary: str
    highlights: list[str] = Field(default_factory=list)
    structured_data: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    estimated_cost: float = 0
    confidence_score: float = 0.0
    tool_summaries: list[str] = Field(default_factory=list)


class DayItem(BaseModel):
    time: str
    title: str
    description: str


class DayPlan(BaseModel):
    day_index: int
    date: str
    city: str
    theme: str
    items: list[DayItem] = Field(default_factory=list)
    hotel_tip: str | None = None
    transport_tip: str | None = None


class BudgetBreakdown(BaseModel):
    transport: float = 0
    hotel: float = 0
    tickets: float = 0
    food: float = 0
    local_transport: float = 0
    buffer: float = 0


class PlanResult(BaseModel):
    plan_id: str
    status: str = "completed"
    summary: str
    days: list[DayPlan] = Field(default_factory=list)
    budget_breakdown: BudgetBreakdown = Field(default_factory=BudgetBreakdown)
    transport_options: list[dict[str, Any]] = Field(default_factory=list)
    hotel_options: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    fallback_plans: list[str] = Field(default_factory=list)
    domain_insights: dict[str, DomainInsight] = Field(default_factory=dict)
    version: int = 1
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AgentTaskRequest(BaseModel):
    task_id: str
    plan_id: str
    agent_type: str
    goal: str
    request: PlanRequest
    shared_context: dict[str, Any] = Field(default_factory=dict)


class ReplanRequest(BaseModel):
    reason: str
    updated_constraints: dict[str, Any] = Field(default_factory=dict)


class PlanEnvelope(BaseModel):
    plan_id: str
    status: str
    request: PlanRequest
    events: list[PlanEvent] = Field(default_factory=list)
    result: PlanResult | None = None
    error: str | None = None
    version: int = 1
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

