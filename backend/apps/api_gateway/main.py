import asyncio
import time

import httpx
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from app.chat_planner import request_chat_decision
from app.config import get_settings
from app.models import (
    ChatPlanningRequest,
    ChatPlanningResponse,
    PlanRequest,
    ReplanRequest,
    ServiceHealth,
    SystemHealthResponse,
)
from app.portal_home import build_portal_home_payload
from app.security import enforce_rate_limit


settings = get_settings()
app = FastAPI(title=f"{settings.api_title} - API Gateway", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _http_error_message(response: httpx.Response, fallback: str) -> str:
    try:
        payload = response.json()
        if isinstance(payload, dict):
            detail = payload.get("detail") or payload.get("message") or payload.get("error")
            if detail:
                return str(detail)
    except ValueError:
        pass
    return fallback


async def _proxy_json(
    method: str,
    base_url: str,
    path: str,
    *,
    json: dict | None = None,
    params: dict[str, int] | None = None,
    timeout: float = 30.0,
    fallback: str,
) -> JSONResponse:
    try:
        async with httpx.AsyncClient(base_url=base_url, timeout=timeout) as client:
            response = await client.request(method, path, json=json, params=params)
            response.raise_for_status()
            return JSONResponse(response.json())
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=exc.response.status_code,
            detail=_http_error_message(exc.response, fallback),
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail=f"{fallback}：上游服务暂不可用") from exc


async def _request_json(
    method: str,
    base_url: str,
    path: str,
    *,
    json: dict | None = None,
    params: dict[str, int] | None = None,
    timeout: float = 30.0,
    fallback: str,
) -> dict:
    try:
        async with httpx.AsyncClient(base_url=base_url, timeout=timeout) as client:
            response = await client.request(method, path, json=json, params=params)
            response.raise_for_status()
            payload = response.json()
            return payload if isinstance(payload, dict) else {"data": payload}
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=exc.response.status_code,
            detail=_http_error_message(exc.response, fallback),
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail=f"{fallback}：上游服务暂不可用") from exc


async def _check_service_health(service: str, url: str) -> ServiceHealth:
    started_at = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(f"{url}/health")
            response.raise_for_status()
            payload = response.json()
            elapsed = int((time.perf_counter() - started_at) * 1000)
            return ServiceHealth(
                service=service,
                status=str(payload.get("status", "ok")),
                url=url,
                latency_ms=elapsed,
                detail=str(payload.get("service", service)),
            )
    except Exception as exc:
        elapsed = int((time.perf_counter() - started_at) * 1000)
        return ServiceHealth(service=service, status="down", url=url, latency_ms=elapsed, detail=str(exc))


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "api-gateway"}


@app.get("/api/v1/system/health")
async def system_health() -> JSONResponse:
    services = [
        ServiceHealth(service="api-gateway", status="ok", latency_ms=0, detail="gateway"),
        *await asyncio.gather(
            _check_service_health("planner-service", settings.planner_service_url),
            _check_service_health("agent-workers", settings.agent_workers_url),
            _check_service_health("mcp-gateway", settings.mcp_gateway_url),
        ),
    ]
    overall = "ok" if all(service.status == "ok" for service in services) else "degraded"
    payload = SystemHealthResponse(status=overall, services=services)
    return JSONResponse(payload.model_dump(mode="json"))


@app.get('/api/v1/portal/home')
async def portal_home() -> JSONResponse:
    payload = build_portal_home_payload()
    return JSONResponse(payload.model_dump(mode='json'))


@app.get("/api/v1/plans/recent")
async def list_recent_plans(limit: int = 8) -> JSONResponse:
    return await _proxy_json(
        "GET",
        settings.planner_service_url,
        "/internal/plans",
        params={"limit": limit},
        fallback="获取最近规划失败",
    )


@app.post("/api/v1/chat/plans", dependencies=[Depends(enforce_rate_limit)])
async def chat_plan(payload: ChatPlanningRequest) -> JSONResponse:
    decision = await request_chat_decision(
        payload.messages,
        payload.llm_config,
        payload.current_request,
        payload.current_plan_id,
    )

    response_payload = ChatPlanningResponse(
        assistant_message=decision['assistant_reply'],
        action=decision['action'],
        status='needs_input',
        request_preview=decision['request_preview'],
    )

    if decision['action'] == 'create_plan' and decision['request_preview'] is not None:
        created = await _request_json(
            'POST',
            settings.planner_service_url,
            '/internal/plans',
            json=decision['request_preview'].model_dump(mode='json'),
            fallback='聊天创建规划失败',
        )
        response_payload.status = str(created.get('status', 'planning'))
        response_payload.plan_id = str(created.get('plan_id'))
        response_payload.stream_url = created.get('stream_url')

    if decision['action'] == 'replan' and payload.current_plan_id:
        replanned = await _request_json(
            'POST',
            settings.planner_service_url,
            f"/internal/plans/{payload.current_plan_id}/replan",
            json={
                'reason': 'chat_replan',
                'updated_constraints': decision['updated_constraints'],
            },
            fallback='聊天重规划失败',
        )
        response_payload.status = str(replanned.get('status', 'planning'))
        response_payload.plan_id = str(replanned.get('plan_id', payload.current_plan_id))
        response_payload.stream_url = replanned.get('stream_url')

    return JSONResponse(response_payload.model_dump(mode='json'))


@app.post("/api/v1/plans", dependencies=[Depends(enforce_rate_limit)])
async def create_plan(payload: PlanRequest) -> JSONResponse:
    return await _proxy_json(
        "POST",
        settings.planner_service_url,
        "/internal/plans",
        json=payload.model_dump(mode="json"),
        fallback="创建规划失败",
    )


@app.get("/api/v1/plans/{plan_id}")
async def get_plan(plan_id: str) -> JSONResponse:
    return await _proxy_json(
        "GET",
        settings.planner_service_url,
        f"/internal/plans/{plan_id}",
        fallback="获取规划失败",
    )


@app.post("/api/v1/plans/{plan_id}/replan", dependencies=[Depends(enforce_rate_limit)])
async def replan(plan_id: str, payload: ReplanRequest) -> JSONResponse:
    return await _proxy_json(
        "POST",
        settings.planner_service_url,
        f"/internal/plans/{plan_id}/replan",
        json=payload.model_dump(mode="json"),
        fallback="重规划失败",
    )


@app.get("/api/v1/plans/{plan_id}/stream")
async def stream_plan(plan_id: str) -> StreamingResponse:
    async def proxy_stream():
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream(
                "GET",
                f"{settings.planner_service_url}/internal/plans/{plan_id}/stream",
            ) as response:
                response.raise_for_status()
                async for chunk in response.aiter_bytes():
                    yield chunk

    return StreamingResponse(proxy_stream(), media_type="text/event-stream")
