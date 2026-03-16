import httpx
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from app.config import get_settings
from app.models import PlanRequest, ReplanRequest
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


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "api-gateway"}


@app.post("/api/v1/plans", dependencies=[Depends(enforce_rate_limit)])
async def create_plan(payload: PlanRequest) -> JSONResponse:
    async with httpx.AsyncClient(base_url=settings.planner_service_url, timeout=30.0) as client:
        response = await client.post("/internal/plans", json=payload.model_dump(mode="json"))
        response.raise_for_status()
        return JSONResponse(response.json())


@app.get("/api/v1/plans/{plan_id}")
async def get_plan(plan_id: str) -> JSONResponse:
    async with httpx.AsyncClient(base_url=settings.planner_service_url, timeout=30.0) as client:
        response = await client.get(f"/internal/plans/{plan_id}")
        response.raise_for_status()
        return JSONResponse(response.json())


@app.post("/api/v1/plans/{plan_id}/replan", dependencies=[Depends(enforce_rate_limit)])
async def replan(plan_id: str, payload: ReplanRequest) -> JSONResponse:
    async with httpx.AsyncClient(base_url=settings.planner_service_url, timeout=30.0) as client:
        response = await client.post(
            f"/internal/plans/{plan_id}/replan",
            json=payload.model_dump(mode="json"),
        )
        response.raise_for_status()
        return JSONResponse(response.json())


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

