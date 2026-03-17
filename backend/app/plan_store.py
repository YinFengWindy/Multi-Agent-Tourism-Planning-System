import asyncio
from datetime import datetime, timezone
from uuid import uuid4

from app.models import PlanEnvelope, PlanEvent, PlanRequest, PlanResult, PlanSummary


def build_plan_summary(envelope: PlanEnvelope) -> PlanSummary:
    return PlanSummary(
        plan_id=envelope.plan_id,
        status=envelope.status,
        version=envelope.version,
        origin_city=envelope.request.origin_city,
        destination_cities=envelope.request.destination_cities,
        travelers=envelope.request.travelers,
        budget=envelope.request.budget,
        summary=envelope.result.summary if envelope.result else envelope.error,
        warning_count=len(envelope.result.warnings) if envelope.result else 0,
        day_count=len(envelope.result.days) if envelope.result else 0,
        created_at=envelope.created_at,
        updated_at=envelope.updated_at,
    )


class PlanStore:
    def __init__(self) -> None:
        self._plans: dict[str, PlanEnvelope] = {}
        self._lock = asyncio.Lock()

    async def create_plan(self, request: PlanRequest) -> PlanEnvelope:
        async with self._lock:
            plan_id = f"plan_{uuid4().hex[:8]}"
            envelope = PlanEnvelope(plan_id=plan_id, status="planning", request=request)
            self._plans[plan_id] = envelope
            return envelope

    async def get(self, plan_id: str) -> PlanEnvelope | None:
        async with self._lock:
            return self._plans.get(plan_id)

    async def restore_plan(self, envelope: PlanEnvelope) -> PlanEnvelope:
        async with self._lock:
            self._plans[envelope.plan_id] = envelope
            return envelope

    async def list_summaries(self, limit: int = 8) -> list[PlanSummary]:
        async with self._lock:
            plans = sorted(self._plans.values(), key=lambda item: item.updated_at, reverse=True)
            return [build_plan_summary(envelope) for envelope in plans[:limit]]

    async def append_event(self, plan_id: str, event: PlanEvent) -> None:
        async with self._lock:
            envelope = self._plans[plan_id]
            envelope.events.append(event)
            envelope.updated_at = datetime.now(timezone.utc)

    async def complete(self, plan_id: str, result: PlanResult) -> None:
        async with self._lock:
            envelope = self._plans[plan_id]
            envelope.status = "completed"
            envelope.result = result
            envelope.updated_at = datetime.now(timezone.utc)

    async def fail(self, plan_id: str, error: str) -> None:
        async with self._lock:
            envelope = self._plans[plan_id]
            envelope.status = "failed"
            envelope.error = error
            envelope.updated_at = datetime.now(timezone.utc)

    async def start_replan(self, plan_id: str, request: PlanRequest) -> PlanEnvelope:
        async with self._lock:
            envelope = self._plans[plan_id]
            envelope.request = request
            envelope.status = "planning"
            envelope.error = None
            envelope.result = None
            envelope.events = []
            envelope.version += 1
            envelope.updated_at = datetime.now(timezone.utc)
            return envelope
