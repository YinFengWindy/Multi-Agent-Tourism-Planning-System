from fastapi import FastAPI

from app.agent_runtime import run_agent_task
from app.config import get_settings
from app.models import AgentTaskRequest
from app.service_clients import HttpToolExecutor


settings = get_settings()
app = FastAPI(title=f"{settings.api_title} - Agent Workers", version="0.1.0")


@app.on_event("startup")
async def startup() -> None:
    app.state.tool_executor = HttpToolExecutor(settings.mcp_gateway_url)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "agent-workers"}


@app.post("/internal/agent-tasks")
async def execute_agent_task(payload: AgentTaskRequest) -> dict:
    result = await run_agent_task(payload, app.state.tool_executor)
    return result.model_dump(mode="json")

