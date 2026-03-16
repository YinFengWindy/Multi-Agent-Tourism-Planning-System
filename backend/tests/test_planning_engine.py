import pytest

from app.agent_runtime import run_agent_task
from app.cache import MemoryCache
from app.models import PlanRequest, ToolExecutionRequest, TravelConstraints
from app.planning_engine import PlanningEngine
from app.tool_runtime import execute_tool


@pytest.mark.asyncio
async def test_tool_runtime_uses_cache() -> None:
    cache = MemoryCache()
    request = ToolExecutionRequest(tool_name="weather_forecast", arguments={"city": "杭州", "date": "2026-05-01"})
    first = await execute_tool(request, cache)
    second = await execute_tool(request, cache)
    assert first.success is True
    assert first.cached is False
    assert second.cached is True


@pytest.mark.asyncio
async def test_planning_engine_generates_result() -> None:
    cache = MemoryCache()

    async def tool_executor(request: ToolExecutionRequest):
        return await execute_tool(request, cache)

    async def agent_executor(request):
        return await run_agent_task(request, tool_executor)

    events = []

    async def emit(event_type: str, message: str, data: dict):
        events.append({"type": event_type, "message": message, "data": data})

    engine = PlanningEngine(agent_executor)
    result = await engine.create_plan(
        "plan_test",
        PlanRequest(
            origin_city="上海",
            destination_cities=["杭州", "乌镇"],
            start_date="2026-05-01",
            end_date="2026-05-03",
            travelers=2,
            budget=4200,
            preferences=["美食", "古镇", "轻松节奏"],
            constraints=TravelConstraints(),
        ),
        1,
        emit,
    )

    assert result.summary
    assert len(result.days) >= 1
    assert "transport" in result.domain_insights
    assert any(event["type"] == "plan_started" for event in events)

