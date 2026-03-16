from datetime import datetime
from typing import Any, Awaitable, Callable

from app.models import AgentTaskRequest, DomainInsight, ToolExecutionRequest, ToolExecutionResponse

ToolExecutor = Callable[[ToolExecutionRequest], Awaitable[ToolExecutionResponse]]


def _trip_days(start_date: str, end_date: str) -> int:
    try:
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
        return max(1, (end - start).days + 1)
    except ValueError:
        return 1


def _primary_city(request: Any) -> str:
    return request.destination_cities[0] if request.destination_cities else request.origin_city


async def _transport_agent(task: AgentTaskRequest, tool_executor: ToolExecutor) -> DomainInsight:
    destination = _primary_city(task.request)
    tool_result = await tool_executor(
        ToolExecutionRequest(
            tool_name="transport_search",
            arguments={
                "origin": task.request.origin_city,
                "destination": destination,
                "travelers": task.request.travelers,
            },
        )
    )
    options = tool_result.data.get("options", [])
    best = options[0] if options else {}
    return DomainInsight(
        agent_type="transport",
        summary=f"推荐 {best.get('mode', '高铁')} 作为主干出行方式，优先兼顾时效与价格。",
        highlights=[
            f"最优出发时间 {best.get('depart_time', '08:00')}",
            f"预计耗时 {best.get('duration_minutes', 90)} 分钟",
            f"单人票价约 {best.get('price', 120)} 元",
        ],
        structured_data={"options": options},
        estimated_cost=float(best.get("price", 120) * max(1, task.request.travelers)),
        confidence_score=0.9,
        tool_summaries=[tool_result.normalized_summary],
    )


async def _hotel_agent(task: AgentTaskRequest, tool_executor: ToolExecutor) -> DomainInsight:
    city = _primary_city(task.request)
    nights = _trip_days(task.request.start_date, task.request.end_date) - 1 or 1
    tool_result = await tool_executor(
        ToolExecutionRequest(
            tool_name="hotel_search",
            arguments={
                "city": city,
                "nights": nights,
                "hotel_level": task.request.constraints.hotel_level,
            },
        )
    )
    options = tool_result.data.get("options", [])
    best = options[0] if options else {}
    return DomainInsight(
        agent_type="hotel",
        summary=f"建议住在 {best.get('district', city)}，便于串联主要景点与交通枢纽。",
        highlights=[
            f"首选酒店 {best.get('name', city + '旅居酒店')}",
            f"评分 {best.get('rating', 4.6)} / 5",
            f"总住宿成本约 {best.get('stay_total', 800)} 元",
        ],
        structured_data={"options": options},
        estimated_cost=float(best.get("stay_total", 800)),
        confidence_score=0.88,
        tool_summaries=[tool_result.normalized_summary],
    )


async def _attraction_agent(task: AgentTaskRequest, tool_executor: ToolExecutor) -> DomainInsight:
    pois_by_city: dict[str, list[dict[str, Any]]] = {}
    highlights: list[str] = []
    tool_summaries: list[str] = []
    for city in task.request.destination_cities or [task.request.origin_city]:
        tool_result = await tool_executor(
            ToolExecutionRequest(
                tool_name="poi_search",
                arguments={"city": city, "preferences": task.request.preferences},
            )
        )
        pois = tool_result.data.get("pois", [])
        pois_by_city[city] = pois
        if pois:
            highlights.append(f"{city}优先景点：{pois[0]['name']}")
        tool_summaries.append(tool_result.normalized_summary)
    return DomainInsight(
        agent_type="attraction",
        summary="已根据城市与兴趣标签筛选核心景点池，用于后续路径编排。",
        highlights=highlights,
        structured_data={"pois_by_city": pois_by_city},
        estimated_cost=0,
        confidence_score=0.87,
        tool_summaries=tool_summaries,
    )


async def _route_agent(task: AgentTaskRequest, tool_executor: ToolExecutor) -> DomainInsight:
    city_plans = []
    tool_summaries: list[str] = []
    for city in task.request.destination_cities or [task.request.origin_city]:
        poi_result = await tool_executor(
            ToolExecutionRequest(
                tool_name="poi_search",
                arguments={"city": city, "preferences": task.request.preferences},
            )
        )
        pois = [poi["name"] for poi in poi_result.data.get("pois", [])[:3]]
        route_result = await tool_executor(
            ToolExecutionRequest(tool_name="route_matrix", arguments={"city": city, "pois": pois})
        )
        city_plans.append(
            {
                "city": city,
                "recommended_pois": route_result.data.get("recommended_order", pois),
                "walking_intensity": route_result.data.get("walking_intensity", "moderate"),
                "theme": f"{city}人文与城市漫步",
            }
        )
        tool_summaries.extend([poi_result.normalized_summary, route_result.normalized_summary])
    return DomainInsight(
        agent_type="route",
        summary="已完成城市内景点顺序与日程节奏编排，优先减少回头路和换乘负担。",
        highlights=[
            f"{item['city']}建议顺序：{' → '.join(item['recommended_pois'])}" for item in city_plans
        ],
        structured_data={"city_plans": city_plans},
        estimated_cost=0,
        confidence_score=0.89,
        tool_summaries=tool_summaries,
    )


async def _budget_agent(task: AgentTaskRequest, tool_executor: ToolExecutor) -> DomainInsight:
    destination = _primary_city(task.request)
    nights = _trip_days(task.request.start_date, task.request.end_date) - 1 or 1
    transport_result = await tool_executor(
        ToolExecutionRequest(
            tool_name="transport_search",
            arguments={
                "origin": task.request.origin_city,
                "destination": destination,
                "travelers": task.request.travelers,
            },
        )
    )
    hotel_result = await tool_executor(
        ToolExecutionRequest(
            tool_name="hotel_search",
            arguments={
                "city": destination,
                "nights": nights,
                "hotel_level": task.request.constraints.hotel_level,
            },
        )
    )
    transport_cost = float(transport_result.data.get("options", [{}])[0].get("price", 120) * task.request.travelers)
    hotel_cost = float(hotel_result.data.get("options", [{}])[0].get("stay_total", 900))
    tickets_cost = 120.0 * max(1, _trip_days(task.request.start_date, task.request.end_date))
    food_cost = 150.0 * max(1, _trip_days(task.request.start_date, task.request.end_date)) * max(1, task.request.travelers)
    local_transport = 40.0 * max(1, _trip_days(task.request.start_date, task.request.end_date))
    buffer = max(300.0, task.request.budget * 0.1)
    total = transport_cost + hotel_cost + tickets_cost + food_cost + local_transport + buffer
    breakdown = {
        "transport": transport_cost,
        "hotel": hotel_cost,
        "tickets": tickets_cost,
        "food": food_cost,
        "local_transport": local_transport,
        "buffer": buffer,
    }
    within_budget = total <= task.request.budget
    warnings = [] if within_budget else [f"当前预估总成本 {round(total, 2)} 元，超出预算 {round(total - task.request.budget, 2)} 元。"]
    return DomainInsight(
        agent_type="budget",
        summary="已完成交通、住宿、门票、餐饮和机动预算拆分。",
        highlights=[
            f"总预算预估 {round(total, 2)} 元",
            f"预算状态：{'可控' if within_budget else '偏紧'}",
            f"建议机动金 {round(buffer, 2)} 元",
        ],
        structured_data={"breakdown": breakdown, "within_budget": within_budget, "total": total},
        warnings=warnings,
        estimated_cost=total,
        confidence_score=0.91,
        tool_summaries=[transport_result.normalized_summary, hotel_result.normalized_summary],
    )


async def _risk_agent(task: AgentTaskRequest, tool_executor: ToolExecutor) -> DomainInsight:
    forecasts = []
    warnings = []
    tool_summaries: list[str] = []
    for city in task.request.destination_cities or [task.request.origin_city]:
        result = await tool_executor(
            ToolExecutionRequest(tool_name="weather_forecast", arguments={"city": city, "date": task.request.start_date})
        )
        forecast = result.data
        forecasts.append(forecast)
        tool_summaries.append(result.normalized_summary)
        if forecast.get("risk_level") == "medium":
            warnings.append(f"{city}存在降雨风险，建议保留室内备选景点。")
    return DomainInsight(
        agent_type="risk",
        summary="已完成天气与行程稳定性评估，生成风险提示和应对建议。",
        highlights=[item.get("advice", "保持弹性") for item in forecasts],
        structured_data={"forecasts": forecasts},
        warnings=warnings,
        estimated_cost=0,
        confidence_score=0.85,
        tool_summaries=tool_summaries,
    )


HANDLERS = {
    "transport": _transport_agent,
    "hotel": _hotel_agent,
    "attraction": _attraction_agent,
    "route": _route_agent,
    "budget": _budget_agent,
    "risk": _risk_agent,
}


async def run_agent_task(task: AgentTaskRequest, tool_executor: ToolExecutor) -> DomainInsight:
    if task.agent_type not in HANDLERS:
        return DomainInsight(
            agent_type=task.agent_type,
            summary=f"{task.agent_type} 暂未实现。",
            confidence_score=0.2,
            warnings=[f"未知 agent 类型：{task.agent_type}"],
        )
    return await HANDLERS[task.agent_type](task, tool_executor)

