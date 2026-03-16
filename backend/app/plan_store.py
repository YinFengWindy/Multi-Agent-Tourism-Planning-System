import asyncio
from datetime import datetime, timezone
from uuid import uuid4

from app.models import PlanEnvelope, PlanEvent, PlanRequest, PlanResult


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

