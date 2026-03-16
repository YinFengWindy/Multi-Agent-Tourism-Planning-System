from fastapi import FastAPI

from app.cache import create_cache
from app.config import get_settings
from app.models import ToolExecutionRequest
from app.tool_runtime import HANDLERS, execute_tool


settings = get_settings()
app = FastAPI(title=f"{settings.api_title} - MCP Gateway", version="0.1.0")


@app.on_event("startup")
async def startup() -> None:
    app.state.cache = await create_cache(settings.redis_url)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "mcp-gateway"}


@app.get("/internal/tools")
async def list_tools() -> dict[str, list[str]]:
    return {"tools": sorted(HANDLERS.keys())}


@app.post("/internal/mcp/execute")
async def mcp_execute(payload: ToolExecutionRequest) -> dict:
    result = await execute_tool(payload, app.state.cache)
    return result.model_dump(mode="json")

