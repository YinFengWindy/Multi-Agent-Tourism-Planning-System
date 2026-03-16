import asyncio
import json
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse

from app.config import get_settings
from app.models import PlanEvent, PlanRequest, ReplanRequest
from app.plan_store import PlanStore
from app.planning_engine import PlanningEngine
from app.service_clients import HttpAgentExecutor
from app.snapshot_store import create_snapshot_store


settings = get_settings()
store = PlanStore()
app = FastAPI(title=f"{settings.api_title} - Planner Service", version="0.1.0")


def _merge_replan_request(plan_request: PlanRequest, payload: ReplanRequest) -> PlanRequest:
    updated = plan_request.model_copy(deep=True)
    for key, value in payload.updated_constraints.items():
        if hasattr(updated, key):
            setattr(updated, key, value)
        elif hasattr(updated.constraints, key):
            setattr(updated.constraints, key, value)
    return updated


def _event_to_sse(event: PlanEvent) -> str:
    data = event.model_dump(mode="json")
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


async def _run_plan(plan_id: str, request: PlanRequest, version: int) -> None:
    async def emit(event_type: str, message: str, data: dict[str, Any]) -> None:
        await store.append_event(plan_id, PlanEvent(type=event_type, message=message, data=data))

    try:
        result = await app.state.engine.create_plan(plan_id, request, version, emit)
        await store.complete(plan_id, result)
        completed = await store.get(plan_id)
        if completed:
            await app.state.snapshot_store.save_plan(completed)
        await emit("plan_completed", "规划已完成，可查看最终行程。", {"plan_id": plan_id, "version": version})
    except Exception as exc:  # pragma: no cover
        await store.fail(plan_id, str(exc))
        failed = await store.get(plan_id)
        if failed:
            await app.state.snapshot_store.save_plan(failed)
        await emit("plan_failed", "规划失败，请检查服务日志。", {"error": str(exc)})


@app.on_event("startup")
async def startup() -> None:
    app.state.engine = PlanningEngine(HttpAgentExecutor(settings.agent_workers_url))
    app.state.snapshot_store = await create_snapshot_store(settings.mongodb_uri, settings.mongodb_db)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "planner-service"}


@app.post("/internal/plans")
async def create_plan(payload: PlanRequest) -> dict[str, Any]:
    envelope = await store.create_plan(payload)
    await app.state.snapshot_store.save_plan(envelope)
    asyncio.create_task(_run_plan(envelope.plan_id, payload, envelope.version))
    return {
        "plan_id": envelope.plan_id,
        "session_id": envelope.plan_id,
        "status": envelope.status,
        "stream_url": f"/api/v1/plans/{envelope.plan_id}/stream",
    }


@app.get("/internal/plans/{plan_id}")
async def get_plan(plan_id: str) -> dict[str, Any]:
    envelope = await store.get(plan_id)
    if not envelope:
        raise HTTPException(status_code=404, detail="plan not found")
    return envelope.model_dump(mode="json")


@app.post("/internal/plans/{plan_id}/replan")
async def replan(plan_id: str, payload: ReplanRequest) -> dict[str, Any]:
    envelope = await store.get(plan_id)
    if not envelope:
        raise HTTPException(status_code=404, detail="plan not found")
    updated_request = _merge_replan_request(envelope.request, payload)
    updated = await store.start_replan(plan_id, updated_request)
    await app.state.snapshot_store.save_plan(updated)
    asyncio.create_task(_run_plan(plan_id, updated_request, updated.version))
    return {
        "plan_id": plan_id,
        "status": updated.status,
        "version": updated.version,
        "stream_url": f"/api/v1/plans/{plan_id}/stream",
    }


@app.get("/internal/plans/{plan_id}/stream")
async def stream_plan(plan_id: str) -> StreamingResponse:
    async def event_generator():
        position = 0
        while True:
            envelope = await store.get(plan_id)
            if not envelope:
                yield "data: {\"type\":\"plan_failed\",\"message\":\"plan not found\"}\n\n"
                return
            events = envelope.events[position:]
            for event in events:
                position += 1
                yield _event_to_sse(event)
            if envelope.status in {"completed", "failed"} and position >= len(envelope.events):
                return
            await asyncio.sleep(0.2)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
