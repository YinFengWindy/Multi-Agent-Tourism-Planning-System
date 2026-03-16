import httpx

from app.models import AgentTaskRequest, DomainInsight, ToolExecutionRequest, ToolExecutionResponse


class HttpToolExecutor:
    def __init__(self, base_url: str, timeout: float = 20.0) -> None:
        self._client = httpx.AsyncClient(base_url=base_url, timeout=timeout)

    async def __call__(self, request: ToolExecutionRequest) -> ToolExecutionResponse:
        response = await self._client.post("/internal/mcp/execute", json=request.model_dump(mode="json"))
        response.raise_for_status()
        return ToolExecutionResponse.model_validate(response.json())


class HttpAgentExecutor:
    def __init__(self, base_url: str, timeout: float = 30.0) -> None:
        self._client = httpx.AsyncClient(base_url=base_url, timeout=timeout)

    async def __call__(self, request: AgentTaskRequest) -> DomainInsight:
        response = await self._client.post("/internal/agent-tasks", json=request.model_dump(mode="json"))
        response.raise_for_status()
        return DomainInsight.model_validate(response.json())

